[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Domain,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string[]]$ExpectedNs,

    [string[]]$Resolvers = @("1.1.1.1", "8.8.8.8")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-Nameserver {
    param([Parameter(Mandatory = $true)][string]$Value)

    return $Value.Trim().TrimEnd(".").ToLowerInvariant()
}

function Get-NameserversFromNslookup {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Server
    )

    $output = (& nslookup -type=ns $Name $Server 2>&1 | Out-String)
    $matches = [regex]::Matches(
        $output,
        "(?im)nameserver\s*=\s*([^\s]+)"
    )

    return @(
        $matches |
            ForEach-Object { Normalize-Nameserver $_.Groups[1].Value } |
            Sort-Object -Unique
    )
}

function Test-NameserverSet {
    param(
        [Parameter(Mandatory = $true)][string[]]$Expected,
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [string[]]$Actual
    )

    if ($Expected.Count -ne $Actual.Count) {
        return $false
    }

    return $null -eq (Compare-Object -ReferenceObject $Expected -DifferenceObject $Actual)
}

$normalizedDomain = $Domain.Trim().TrimEnd(".").ToLowerInvariant()
$normalizedExpected = @(
    $ExpectedNs |
        ForEach-Object { Normalize-Nameserver $_ } |
        Sort-Object -Unique
)

if ($normalizedExpected.Count -lt 1) {
    throw "ExpectedNs must contain at least one nameserver."
}

$failed = $false

foreach ($resolver in $Resolvers) {
    $actual = @(Get-NameserversFromNslookup -Name $normalizedDomain -Server $resolver)
    if (Test-NameserverSet -Expected $normalizedExpected -Actual $actual) {
        Write-Host "[PASS] Resolver $resolver -> $($actual -join ', ')"
    }
    else {
        Write-Host "[FAIL] Resolver $resolver -> $($actual -join ', ')" -ForegroundColor Red
        Write-Host "       Expected -> $($normalizedExpected -join ', ')"
        $failed = $true
    }
}

$authoritativeServer = $normalizedExpected[0]
$authoritativeAddress = $null
try {
    $authoritativeAddress = Resolve-DnsName `
        -Name $authoritativeServer `
        -Type A `
        -Server $Resolvers[0] `
        -DnsOnly `
        -ErrorAction Stop |
        Where-Object { $_.Type -eq "A" } |
        Select-Object -First 1 -ExpandProperty IPAddress
}
catch {
    Write-Verbose "Could not resolve an IPv4 address for $authoritativeServer."
}

$authoritativeQueryServer = if ($authoritativeAddress) {
    $authoritativeAddress
}
else {
    $authoritativeServer
}

$authoritativeNs = @(
    Get-NameserversFromNslookup -Name $normalizedDomain -Server $authoritativeQueryServer
)

if (Test-NameserverSet -Expected $normalizedExpected -Actual $authoritativeNs) {
    Write-Host "[PASS] Authoritative $authoritativeServer ($authoritativeQueryServer) -> $($authoritativeNs -join ', ')"
}
else {
    Write-Host "[FAIL] Authoritative $authoritativeServer ($authoritativeQueryServer) -> $($authoritativeNs -join ', ')" -ForegroundColor Red
    Write-Host "       Expected -> $($normalizedExpected -join ', ')"
    $failed = $true
}

$soaOutput = (& nslookup -type=soa $normalizedDomain $authoritativeQueryServer 2>&1 | Out-String)
if ($soaOutput -match "(?im)primary name server\s*=") {
    Write-Host "[PASS] SOA returned by $authoritativeServer"
}
else {
    Write-Host "[FAIL] No SOA returned by $authoritativeServer" -ForegroundColor Red
    $failed = $true
}

if ($failed) {
    exit 1
}

Write-Host "NS migration verification passed for $normalizedDomain."
exit 0
