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

## Follow-up: X11-test1 boot trace and corrected ABI-property patch

**Test archive:** `X11-test1.zip` (Android 13 host; Android 11 guest; rootless tawcroot)

### What the trace confirmed

The host diagnostic says `Host AArch32: no`, yet guest init evaluates the `ro.product.cpu.abilist32=* && early-init` trigger and starts `boringssl_self_test32`. That executable fails with `Exec format error`; the service's `reboot_on_failure` causes shutdown. The repeated `reboot call returned: Function not implemented` is during the shutdown/reboot attempt, after the fatal trigger—not the initial cause.

The uploaded `guest-logcat.txt` says `instance is not running`, and `engine-logs/init.log` only records `init exited: 139`; neither contains guest userspace diagnostics before the failure. `kmsg.txt` contains the useful early-init sequence.

### Two omissions in the first repair

1. The 64-bit-only property rewrite did not include `/system/product/etc/build.prop`, where Android 11 Product ABI properties can remain declared.
2. The property parser's partition-prefix matching did not correctly match the base key `ro.product.cpu.abilist32`. Merely adding Product's build.prop to the file list would still leave this key unmodified.

### Correction committed

The rootless helper patch now:
- Includes `/system/product/etc/build.prop` in the 64-bit-only property rewrite.
- Explicitly rewrites the base `ro.product.cpu.abilist` to `arm64-v8a`.
- Explicitly clears the base `ro.product.cpu.abilist32`.
- Retains the existing partition-prefixed property handling and `ro.zygote` rewrite.

**Correction commit:** `dd646d076a6c7b0568ec5d5687482f720eacb06e`.

### Build #34 verification

Workflow run **#34** (`44273995216`) completed successfully for the correction commit:
- All 18 build, merge, signature, native-library, and upload steps succeeded.
- Artifact ID: `14414276778`.
- APK SHA-256: `cd5d37482e06a8baa4a7b790cab8a70c47d73fef8b053b08f0d97fccb406eb37`.
- APK size: **79,698,460 bytes**; 286 ZIP entries.
- All 16 required ARM64 libraries were present; APK signing verification passed in CI.

A local entry comparison against Build #31's complete APK found the same **286 entry paths** and identical file size. Only four entries had changed hashes: `lib/arm64-v8a/libvine_helper.so` (the intended helper rebuild) and the three APK signing metadata entries. No other APK entry changed in that comparison.

**Runtime testing is still pending**. This build is a candidate for the next device test; a successful CI/package comparison does not itself prove Android 11 boots.


## Follow-up correction: X11-test1 failure and Build #36

### Additional finding
The prior correction wrote `ro.product.cpu.abilist32=` (an empty property value) rather than removing the property line. Because Android init wildcard property triggers may still match a defined property even when its value is empty, clearing the value was not a sufficiently safe way to suppress the `abilist32=* && early-init` trigger. The correction now removes the base `ro.product.cpu.abilist32` line entirely from sanitized build.prop files. This is a focused change to `scripts/patch_helper.py`; it does not alter Build 61 APK restoration, native libraries, other ABI properties, or signing.

### Build #36
- Commit: `d252e9b42ff8a8e9bf4014dadbab1f224f0e102c`
- Workflow run: [#36](https://github.com/Cutie-Cookie/NestBox/actions/runs/44276027841), completed successfully.
- Artifact: `NestBox-arm64-v8a-debug-complete` (ID `14413794494`), not expired at build time.
- Workflow steps all passed, including native builds, 16 required ARM64 library checks, Gradle packaging, original APK restoration/re-signing, and final APK verification/upload.
- Downloaded artifact locally and verified ZIP/APK integrity. APK SHA-256: `9ffe7419af70528ebbcf5b715594ac04d1aaec0189d4fc1d53528c15b1bf8881`.
- APK has 286 ZIP entries and 22 ARM64 native-library entries; all 16 workflow-required libraries are present.
- Build 61 original-only libraries `libOpenglRender.so`, `libloader.so`, and `libtwoyi.so` are present.
- CI signing verification passed; CI reported v3 signing enabled. The artifact is the exact APK downloaded from run #36.

### Remaining validation
This is still a test candidate, not a proven boot fix. The only decisive next check is runtime testing on the Android 11 guest in the user's device/ROM. Record whether the guest proceeds past the `boringssl_self_test32` init trigger and whether a new failure appears.
