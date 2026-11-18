# Build 61 Packaging Regression and Android 11 AArch32 Repair

**Date:** 2026-11-18  
**Branch:** `fix/android11-aarch32-detection`  
**Purpose:** Record the changes made, the packaging regression discovered, and the lessons learned. This is a technical history—not a future-work instruction checklist.

## Baseline

Build 61 was identified by the user as the last known working NestBox build before the Android 11 compatibility work. It is the reference for the full app contents and packaging process.

## Android 11 boot failure investigated

The boot log showed an attempt to execute `/system/bin/boringssl_self_test32` failing with `Exec format error`, followed by a reboot reason `boringssl-self-check-failed`.

The 32-bit self-test executable was present and executable, but the host could not execute it. The investigation found that Android ABI properties alone could overstate whether the host kernel actually supports running AArch32 userspace. The compatibility patch changed the helper's AArch32 detection to prioritize kernel evidence and use Android ABI properties only as a fallback.

## Packaging regression found

The first Android 11 fix workflow was simplified and did not carry forward Build 61's original APK restoration/merge step. This produced a smaller APK and dropped original-only package entries. The reduced APK was about 73.3 MB, versus roughly 79.7 MB for Build 61. The difference was not just compression: original APK-only files and resources were absent.

The missing original content included native components such as:
- `libOpenglRender.so`
- `libloader.so`
- `libtwoyi.so`

It also included original DEX backup/preservation content and Apache Commons language resources. The initial comparison identified 136 missing entry paths in the reduced build.

## Restoration work

The Build 61 packaging pipeline was restored on the Android 11 fix branch, including the original APK merge/restoration stage and native build/patch support scripts. The Android 11 AArch32 helper patch was retained.

The restored workflow now:
1. Fetches the pinned Wayondroid source and runtime dependencies.
2. Builds the patched native components, including `tawcroot` and the rootless helper.
3. Checks required native library outputs before Gradle packaging.
4. Restores the signing keystore from the repository's existing Actions secrets (`NESTBOX_KEYSTORE_BASE64` and `NESTBOX_KEYSTORE_PASSWORD`).
5. Builds the APK.
6. Restores original APK-only entries and re-signs the resulting package.
7. Verifies required libraries and package/signature checks before uploading the artifact.

## Build verification recorded

**Workflow Build #31 — run ID 44270111565 — completed successfully.**

Recorded checks from its logs:
- Build job and all steps completed successfully.
- Original APK merge reported **281 original entries** inspected.
- **131 original-only entries** were added back.
- **0 obsolete original signature entries** were retained (package was re-signed).
- Original non-signature entry paths were verified.
- Original `classes14.dex` was preserved byte-for-byte as an asset, while unique classes were retained in runtime `classes14.dex`.
- **All 16 required ARM64 native libraries** were present.
- APK signature verification reported **v3 scheme true**.
- APK size reported approximately **77M** (the artifact package size differs from the APK size; avoid confusing those figures).

The workflow uploaded artifact `NestBox-arm64-v8a-debug-complete` (artifact ID `14411758711`). The artifact was downloaded into this session for delivery, but the generated local copy path should be treated as session-specific.

## What we learned

- A successful Gradle build does not prove the APK is complete; compare contents against the known-good baseline.
- Workflow simplification can silently omit essential post-build steps.
- APK size is a useful warning signal, not sufficient proof of missing or preserved contents.
- Original APK-only restoration and signing must happen after the new fix is packaged, in the established order.
- A build's green status is not enough: native-library checks, restoration checks, entry-path comparison, and signature verification are important.
- Build 61 should remain the comparison baseline for future regressions, unless the user explicitly approves a new baseline.

## Testing status

CI build and packaging checks passed. **Runtime testing on the user's device/ROM is not yet confirmed**; awaiting the user's test report.
