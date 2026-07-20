---
name: ship-wpf-github-release
description: >
  Build, repair, and verify a Windows WPF CI and GitHub Release pipeline. Use when
  a WPF repository needs SDK pinning, PowerShell build orchestration, deterministic
  desktop tests, self-contained win-x64 publishing, an installer, tag-based releases,
  or diagnosis of setup-dotnet, runner, packaging, artifact, and gh CLI failures.
---

# Ship WPF GitHub Release

## Outcome

Create one repeatable Windows build contract that works locally, in pull-request CI,
and in a tag-triggered release. Keep WPF build logic in a versioned PowerShell driver;
the workflows should select tools, pass metadata, upload outputs, and report failures.

Read [workflow-patterns.md](references/workflow-patterns.md) when authoring or refactoring
the driver/workflows. Read [failure-playbook.md](references/failure-playbook.md) when a
runner, installer, UI test, or release fails.

## Workflow

### 1. Discover the repository

Inspect repository instructions, the solution/project files, target frameworks, existing
test projects, version source, installer definition, and every workflow under
`.github/workflows/`. Preserve existing packaging and signing decisions. Do not invent a
second build path for CI if a checked-in deploy script already exists.

### 2. Pin the SDK and working directory

Match `global.json` to the WPF target framework (for example, a .NET 9 app uses a
9.0 feature band) and use `actions/setup-dotnet` for the same major line. Verify the
selected `dotnet --version` in the job and fail if it is not the expected major. A
runner can have several SDKs: setup-dotnet installs one but does not necessarily make
it the selected SDK. The driver must `Push-Location` to the repository root before
restore/build/publish so `global.json` is actually discovered, then restore the location
in `finally`.

Only keep a custom `dotnet.exe` resolver when local developer profiles need it. If it
probes candidate executables, temporarily set `DOTNET_ROOT` and `DOTNET_ROOT_X64` to the
candidate root, capture and restore their original values, and reject a candidate whose
reported version is outside the target line.

### 3. Put build policy in PowerShell

Expose a small set of modes such as `Quick`, `Ci`, and `Installer`:

- `Quick`: publish the self-contained Windows executable for fast local iteration.
- `Ci`: restore, Release build, unit tests, deterministic WPF UI tests, and publish.
- `Installer`: restore/build/unit tests, publish, compile the installer, generate a
  checksum, and run the install/launch/uninstall smoke test.

Use `--no-restore` and `--no-build` only after the corresponding step succeeded. Resolve
all paths from the repository root, refuse to delete a drive root/user profile/repository
root when resetting output directories, and write stable paths to `GITHUB_OUTPUT` when
the script is called by Actions. Keep release version metadata in one authoritative
source and pass it to both `dotnet publish` and the installer.

### 4. Make desktop tests deterministic

WPF UI tests must be able to run without a human or a long-lived desktop process. Add a
test/acceptance switch that bypasses external browser/device initialization, launches a
known window, checks automation IDs and key controls, writes screenshots and failure logs
to a job-provided directory, and exits. Every process needs a timeout plus kill fallback.
Upload UI artifacts with `if: always()` so a failed test remains diagnosable.

### 5. Package and smoke-test

Prefer the repository's existing installer technology. For a classic unpackaged WPF app,
Inno Setup is a practical default: publish `win-x64 --self-contained true`, inject a
validated semantic version, compile with a compiler resolved from an explicit environment
override, per-user install path, Program Files, and `PATH`, then write `SHA256SUMS.txt`.
Install the compiler explicitly on hosted runners. Pin any downloaded language/resource
file to a commit and verify its SHA-256; do not depend on a moving branch.

The smoke test must silently install into a unique temporary directory, launch the installed
executable in the deterministic screenshot mode, require exit code zero and the screenshot,
locate the uninstaller, silently uninstall, and verify application files are gone. Clean up
in `finally`, including processes and temporary directories.

### 6. Separate CI from release

The normal CI workflow runs on Windows for pushes and pull requests, calls the same driver,
and uploads the self-contained app plus UI artifacts. Keep permissions read-only. The release
workflow runs on `v*` tags and supports `workflow_dispatch` with a version and an optional
release tag. Give only the release job `contents: write`, pass `GH_TOKEN`, and use `gh` to
create/find the release and upload the installer plus checksum. Check current official action
major versions when editing; do not cargo-cult old versions.

### 7. Prove the release before tagging

Run parser checks, local build/test/smoke checks, and a remote `workflow_dispatch` with an
empty release tag first. Inspect the run with `gh run view --log-failed` or `gh run watch
--exit-status`. Only after that succeeds should a new tag be pushed. Never force-move a tag
that already triggered a public run; use a new patch tag. After release, inspect assets with
`gh release view`, download the checksum, and compare it with the asset digest.

## Validation checklist

- PowerShell scripts parse with the Windows PowerShell parser.
- `global.json`, workflow SDK input, and the driver select the same target SDK line.
- Local `Quick`, `Ci`, and `Installer` modes work on a clean Windows checkout as available.
- CI has stable artifact paths and `if-no-files-found: error`.
- UI and installer processes have bounded lifetimes and cleanup.
- Release metadata rejects malformed tags/versions and does not create a release in dry-run.
- Release permissions are scoped to contents write only where upload is needed.
- `git diff --check` and the repository's structural/language validators pass.

For failure-specific symptoms and fixes, use the failure playbook rather than silently
loosening checks or retrying a release with a mutable tag.
