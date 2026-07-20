# WPF CI and Release failure playbook

Use the symptom first, then fix the contract that caused it. Keep failed run IDs and
their logs in the change record when the repair is non-obvious.

| Symptom | Cause | Repair |
| --- | --- | --- |
| `setup-dotnet` succeeds but the driver says the target SDK is missing | The driver only searched the user install or a hard-coded path; hosted runners place the SDK elsewhere | Prefer `global.json` plus `setup-dotnet`; if a resolver remains, probe `DOTNET_ROOT_X64`, `DOTNET_ROOT`, and `PATH` and log every candidate |
| The resolver sees a candidate but reports a newer SDK (for example, 10.x instead of 9.x) | `dotnet.exe` is a muxer and inherited `DOTNET_ROOT` changes which SDK it selects; runners contain multiple SDKs | Set both root variables to the candidate root while probing and restore them; then add `global.json` so every build command selects the intended line |
| `global.json` exists but CI still selects the wrong SDK | The script was invoked outside the repository and never changed to the directory containing `global.json` | `Push-Location` to the repo root around all restore/build/publish work and `Pop-Location` in `finally` |
| Local PowerShell chooses the wrong SDK after setup | A profile, `MSBuildSDKsPath`, multilevel lookup, or an older PATH entry overrides the tool | Make the setup script idempotent, set `DOTNET_ROOT`, `DOTNET_ROOT_X64`, and `DOTNET_MULTILEVEL_LOOKUP` for the process, remove stale `MSBuildSDKsPath`, put the selected root first, and print `dotnet --info` |
| `ISCC.exe` is not found locally while Inno is installed | Inno was installed per-user, not under Program Files | Search an explicit override, `%LOCALAPPDATA%\Programs\Inno Setup 6`, both Program Files locations, and `PATH` |
| `ISCC.exe` is not found on the runner | The hosted image does not include the expected compiler or its path changed | Install Inno in the workflow, resolve the actual path, and fail with a diagnostic instead of assuming one location |
| Inno fails because a language file is missing | The `.iss` references `compiler:Languages\...` but the runner package lacks that file | Pin/download the resource from a fixed commit, verify SHA-256, and reference the checked-in/downloaded local file |
| Inno compiler accepts local files but fails on a fresh checkout | Output/publish directories or language assets were present only on the developer machine | Start from a clean checkout in CI; make the driver create every directory and validate every input |
| The app or installer smoke step hangs | The normal WPF app waits for a human, WebView2, device, or network initialization | Add an explicit acceptance mode that bypasses external initialization, writes a deterministic screenshot, exits, and has a 30-second process timeout plus kill fallback |
| UI tests pass but no screenshots/logs are available | Artifacts were written beside the test binary or uploaded only on success | Route paths from an environment variable such as `WPF_UI_ARTIFACTS`; upload with `if: always()` and `if-no-files-found: error` |
| Installed app launches but smoke test never finishes | Installer smoke launched the production app without a test switch | Propagate the same acceptance/screenshot environment to the installed executable and assert both exit code and screenshot existence |
| Uninstall returns success but files remain | The test did not find the real uninstaller or did not verify the install directory | Locate the generated uninstaller, run it silently, assert exit code, and check the expected executable/files are gone before cleanup |
| PowerShell parser rejects `WaitForExit(30_000)` | A numeric separator was parsed differently by the runner's PowerShell version/context | Use a plain integer such as `30000`; parse every `.ps1` with the Windows PowerShell parser before pushing |
| Release workflow builds an artifact but no GitHub Release asset appears | The manual run intentionally had an empty release tag, or `GH_TOKEN`/permissions are missing | Treat empty `release_tag` as build-only; for upload set `GH_TOKEN` from `github.token` and `permissions: contents: write`, then inspect `gh auth status`/job logs |
| `gh run view` shows only status or annotations, not job logs | Public REST endpoints do not expose full job logs without sufficient authorization | Authenticate `gh` against the repository and use `gh run view <id> --log-failed`; do not infer the cause from a green/failed summary alone |
| Release asset upload reports a missing file | Workflow path and driver output path diverged, or a glob matched zero files | Emit absolute paths through `GITHUB_OUTPUT`, upload a stable known directory, and use `if-no-files-found: error` |
| A failed release tag needs a code fix | Tags trigger workflows immediately and are immutable in the release process | Do not force-move a visible tag. Run a dry-run workflow on the fixed commit, then publish a new patch tag |
| Checksum in the release is wrong | Checksum was computed before the final installer was produced, or the wrong asset was uploaded | Generate it beside the final installer, download the published checksum, and compare with the GitHub asset digest from `gh release view` |
| YAML step fails before PowerShell starts | A folded scalar, GitHub expression, quoting, or indentation changed the command | Use `shell: pwsh`, block scalars for scripts, quote paths, write step outputs with `$env:GITHUB_OUTPUT`, and run a YAML parser before dispatch |
| Actions workflow uses an old runtime/action major | Workflow was copied from an older repository and hosted runners changed | Check current official action documentation/release notes and update majors deliberately; keep build behavior in the script so action upgrades stay small |
| Version differs between executable, installer, and release | Several files or workflow inputs own the version | Choose one source (for example `Directory.Build.props` or the validated tag), derive file version once, and pass the same values to publish, Inno, artifact names, and release notes |
| Build is green but unsigned installer is blocked by SmartScreen | CI created a valid package but no signing identity was configured | Report signing as a separate release prerequisite. Do not claim trust or silently add a secret; sign only in a protected job when certificates/secrets are available |

## Diagnostic commands

```powershell
gh run list --workflow <workflow> --limit 10
gh run view <run-id> --log-failed
gh run watch <run-id> --exit-status
gh release view <tag> --json assets,url
gh auth status
```

For a local reproduction, run the driver in `Quick`, then `Ci`, then `Installer` mode
with a unique output path. Record `dotnet --info`, the resolved `ISCC.exe`, the generated
installer path, and the checksum before changing the workflow.
