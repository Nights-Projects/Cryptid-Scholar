## APK Build + GitHub Release Deployment

### What was implemented
The `.github/workflows/build-apk.yml` workflow now:
1. **Auto-versioning**: Reads `versionCode` from `android/app/build.gradle.kts`, increments by 1 on each build
2. **Release tags**: Creates Git tags in `alpha-1.XX` format where XX is zero-padded (e.g., `alpha-1.02`, `alpha-1.03`, ...)
3. **GitHub Releases**: Each successful build creates a GitHub Release (prerelease) with:
   - Both debug and release APK uploaded as release assets (`cryptid-scholar-vX.apk`, `cryptid-scholar-vX-debug.apk`)
   - Generated release notes
4. **Workflow artifacts**: APK also uploaded as workflow artifact for direct download without release

### Current state
- `versionCode = 2` on main (the last successful build was #54 which produced `alpha-1.02`)
- Next workflow run will read `versionCode=2`, increment to `3`, and create release `alpha-1.03`
- **Note**: The very first build (run #54) produced `alpha-1.02` instead of `alpha-1.01` because the versionCode started at 1 and the workflow increments BEFORE using it for the tag

### Files
- `.github/workflows/build-apk.yml` — the workflow with versioning + deployment
- `android/app/build.gradle.kts` — versionCode tracking (currently 2)

### Future builds
- Trigger: push to `android/**`, PR to main, or manual dispatch
- Each run increments `versionCode` and creates `alpha-1.XX` release
- Old releases are cleaned up; only the latest one remains
