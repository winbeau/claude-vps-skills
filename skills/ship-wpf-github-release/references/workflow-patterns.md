# WPF workflow patterns

Use these as implementation shapes, not copy-paste product code. Keep names, paths, and
the installer technology aligned with the target repository.

## SDK selection

At the repository root, commit a `global.json` that matches the target framework. For a
.NET 9 WPF application, a typical policy is:

```json
{
  "sdk": {
    "version": "9.0.300",
    "rollForward": "latestFeature",
    "allowPrerelease": false
  }
}
```

Use the installed feature band that the repository supports. `rollForward` should be an
explicit policy, not an accidental runner default. In every Windows job:

```yaml
- uses: actions/setup-dotnet@<current-stable-major>
  with:
    dotnet-version: "9.0.x"
- name: Verify selected SDK
  shell: pwsh
  run: |
    $version = dotnet --version
    if ($version -notmatch '^9\.') { throw "Unexpected SDK: $version" }
    dotnet --info
```

The action major is intentionally a placeholder: inspect the current official action
before editing. `dotnet-version` installs a line; `global.json` selects it.

### Persistent local PowerShell selection

When the user explicitly wants the selected SDK to persist across terminals, keep that
machine-level convenience separate from repository correctness. Write an idempotent,
marker-delimited block into the PowerShell 7 and/or Windows PowerShell profile:

```powershell
# >>> project .NET toolchain >>>
$toolRoot = Join-Path $HOME ".dotnet"
$toolExe = Join-Path $toolRoot "dotnet.exe"
if (Test-Path -LiteralPath $toolExe) {
    $env:DOTNET_ROOT = $toolRoot
    $env:DOTNET_ROOT_X64 = $toolRoot
    $env:DOTNET_MULTILEVEL_LOOKUP = "0"
    Remove-Item Env:MSBuildSDKsPath -ErrorAction SilentlyContinue
    $otherPaths = @($env:Path -split ';' | Where-Object {
        $_ -and -not $_.TrimEnd('\').Equals(
            $toolRoot.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)
    })
    $env:Path = (@($toolRoot) + $otherPaths) -join ';'
}
# <<< project .NET toolchain <<<
```

The setup script should replace its own marked block instead of appending duplicates,
create a missing profile directory, validate the selected `dotnet.exe --version` first,
and update the current process as well as future shells. A profile is not a substitute
for `global.json`: CI and clean clones must remain correct without user profile state.

## PowerShell driver

The driver should own restore, build, test, publish, packaging, and smoke-test policy.
Its outer shape should restore the caller's directory even when invoked from a workflow
or another directory:

```powershell
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Push-Location $repoRoot
try {
    # Resolve the target SDK, then run all dotnet commands here.
    # Resolve version and output paths from $repoRoot.
}
finally {
    Pop-Location
}
```

Recommended command order:

```text
restore solution
build solution --configuration Release --no-restore
test unit project --configuration Release --no-build
test UI project --configuration Release --no-build (CI mode)
publish app --configuration Release --runtime win-x64 --self-contained true
```

The publish directory is a unique/resettable path. Reject unsafe reset targets before
`Remove-Item -Recurse -Force`. Check that the expected `.exe` exists after publish.
When called by Actions, append `name=value` records to `$env:GITHUB_OUTPUT`; do not make
the workflow guess a path from a glob.

If local profiles need a pinned `dotnet.exe`, an opt-in resolver may inspect an explicit
environment override, `DOTNET_ROOT_X64`, `DOTNET_ROOT`, the user install, and `PATH`.
For each candidate, temporarily set both `DOTNET_ROOT` variables to its parent before
running `--version`, then restore both variables in `finally`. The normal CI path should
prefer `setup-dotnet` plus `global.json`.

## Deterministic WPF UI test

Use an environment variable or command-line flag that the application and test agree on:

```text
WPF_UI_TEST=1
WPF_UI_ACCEPTANCE=1
WPF_SCREENSHOT_THEME=HighContrast
WPF_SCREENSHOT_PATH=<job temp>\cockpit-highcontrast.png
WPF_FAILURE_LOG=<job temp>\terminal-failures.log
```

In acceptance mode, skip WebView2/device/network initialization and render a stable
placeholder or local fixture. The test should launch the app, assert automation IDs and
important controls, close/kill it in `finally`, then launch the screenshot path as a
separate process and require it to exit within a fixed timeout. Use a real job artifact
directory and upload it even on failure.

Do not make a normal interactive WPF launch part of CI. A window that waits for a human,
WebView2 runtime, camera, or device will look like a hung build rather than a useful test.

## Installer and checksum

For Inno Setup, resolve the compiler in this order: an explicit repository environment
variable, the per-user install under `%LOCALAPPDATA%`, Program Files locations, then
`Get-Command ISCC.exe`. Hosted Windows jobs should install Inno explicitly (for example,
through the runner's package manager) and still verify the executable exists.

Pass semantic and file versions separately. A prerelease such as `1.2.3-rc.1` should use
`1.2.3.0` for Windows file metadata while retaining the full semantic version in the
installer name and release notes. Compile one installer, fail if the count is not exactly
one, calculate SHA-256 with `Get-FileHash`, and write an ASCII checksum file beside it.

If the installer references a language file that is absent on a fresh runner, download a
fixed upstream commit and verify its expected hash before compiling. Prefer committing a
small stable resource when licensing allows.

## Workflow split

CI should be structurally similar to:

```yaml
name: CI
on: [push, pull_request]
jobs:
  wpf:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@<current-stable-major>
        with: { submodules: recursive }
      - uses: actions/setup-dotnet@<current-stable-major>
        with: { dotnet-version: "9.0.x" }
      - shell: pwsh
        run: ./deploy/build-wpf.ps1 -Mode Ci -PublishPath "${{ runner.temp }}\wpf-publish"
      - if: always()
        uses: actions/upload-artifact@<current-stable-major>
        with:
          name: wpf-ui-artifacts
          path: ${{ runner.temp }}\ui-artifacts
          if-no-files-found: error
```

Release should support both a tag and a build-only manual run:

```yaml
on:
  push:
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      version: { required: true, type: string }
      release_tag: { required: false, default: "", type: string }
permissions:
  contents: write
```

Resolve the version from the tag on `push`, validate semver, and write `version`,
`file_version`, and `release_tag` through `$GITHUB_OUTPUT`. Always upload a workflow
artifact. Only when `release_tag` is non-empty should the job run `gh release view`,
`gh release create` if necessary, and `gh release upload --clobber` with `GH_TOKEN`.

## Dry-run and release verification

The safe sequence is:

```powershell
gh workflow run <release-workflow> --ref main -f version=1.2.3 -f release_tag=
gh run watch <run-id> --exit-status
gh run view <run-id> --log-failed
git tag v1.2.3
git push origin v1.2.3
gh run watch <tag-run-id> --exit-status
gh release view v1.2.3 --json assets,url
```

The first run proves the installer without mutating a GitHub Release. Failed public tags
are not repaired by force-pushing a new commit under the same tag; push a new patch tag.
