# NestBox Android 11 rootless boot repair — work log

## Goal and acceptance criteria
Fix the Android 11 guest boot failure found in user test archive `X11-test2.zip`, deliver a signed APK built through the complete Build 61-based restoration/merge/signing workflow, and leave a detailed record of actions and failures.

No runtime fix is considered successful until a device test log confirms the guest stays booted. APK delivery also requires successful CI, signature verification, native library verification, and comparison of APK entries to the Build 61 baseline. A CI build alone is not proof of runtime success.

## Baseline / evidence
- Baseline APK: Build 61 (preservation priority).
- Existing repair branch head at start: `f57b00fbed150846916ce16779ae72836b22bd5f`.
- Prior device report archive: `X11-test2.zip`.
- Host/device context from that report: Android 13 host, ARM64 host ABI list includes ARM32 ABIs but rootless exec capability is unavailable.
- Guest: Android 11 LineageOS 18.1 Waydroid ARM64.
- Host AArch32: no.
- The 64-bit BoringSSL tests passed. The observed reboot reason is `bpfloader-failed`; `bpfloader` exits status 2. Its exact internal error was not captured in the archive.
- Logs also show the old `init.zygote64_32.rc` is still imported and `app_process32` cannot execute (Exec format error). These are observed compatibility problems; their causal link to bpfloader failure is not proven.
- A separate shutdown-time `vold` crash is observed in `AbortFuseConnections()` while attempting to iterate `/sys/fs/fuse/connections` (Permission denied). Treat as secondary, not the initial boot trigger.

## Investigation diary
### Step 1 — 2026-11-18: inspect test archive and existing patch
- Reviewed the user-provided X11-test2 log bundle and existing `scripts/patch_helper.py`.
- Confirmed property sanitization already targets `/system/product/etc/build.prop` and explicitly rewrites/removes ABI list properties.
- Confirmed helper still creates a standalone `init.zygote64.rc` from the 64_32 file; this does not prove the original import was replaced.
- Confirmed workflow pins Wayondroid source commit `a45f80b1aaa463d199c9056bb8dda7c01be5ece7`.
- Confirmed complete packaging workflow restores original APK-only entries via `scripts/merge_original_apk.py`, re-signs, verifies signature/certificate, checks ARM64 native libraries, and uploads artifact. These steps must remain unchanged.
- Created isolated repair branch `fix/android11-rootless-boot-repair` from the existing repair head to avoid overwriting that branch.

## Step-by-step changes and test results
(Each new action, patch, CI attempt, error, correction, and verification result is appended below. Failures are retained, not erased.)

### Step 2 — 2026-11-18: targeted boot repair implemented; first CI attempt failed
- Added rootless-only repair code to `scripts/patch_helper.py` that backs up `init.zygote64_32.rc` to the instance's `nestbox-original` directory and rewrites the actual imported file to the 64-bit-only portion. The generated `init.zygote64.rc` is also written.
- Added a targeted `bpfloader.rc` edit that backs up the original rc and removes only `reboot_on_failure` from the bpfloader service stanza. It does not disable the service or trigger. This is a mitigation to allow Android to continue when rootless BPF loading is unsupported; it does not claim BPF functionality is fixed.
- Added a workflow branch trigger for `fix/android11-rootless-boot-repair` to allow isolated CI.
- First CI attempt (run #40, ID `44280151250`) **failed** during native compilation of `rootless_prep.cpp`: `VINE_LOGW` was unavailable in that translation unit at the two new diagnostic calls. The failure was limited to diagnostics, not the zygote/bpf policy logic.
- Correction committed: replaced those calls with `fprintf(stderr,...)`, which is available via the existing `cstdio` include. Rebuild triggered automatically by push.
- Next: verify script patch application, native compile, full APK merge/sign checks, and download artifact for local APK entry comparison. ### Step 3 — 2026-11-18: build and packaging verification (run #42)
- CI run `44280629928` completed successfully. All steps passed, including native compilation, required ARM64 library checks, Gradle APK build, restoration/merge of original APK-only entries, zipalign, re-signing, and final APK verification.
- CI verified APK signing with APK Signature Scheme v3, one signer, and 16 required ARM64 libraries. Local APK extraction confirms 22 ARM64 native library entries.
- Downloaded the exact run #42 artifact and APK into the verification workspace. APK SHA-256: `c36d8fc1bebea2d6ddc4f6b038877b0b75bbe4d0a4496128a07bc9e643b426f9`. APK size: 79,698,460 bytes.
- Locally checked signature with `jarsigner -verify` (valid). Extracted signer certificate SHA-256 fingerprint matches permanent NestBox release certificate: `1D:D1:CF:B8:84:6E:F3:DD:B4:39:C1:C8:B2:32:F2:C4:0F:90:75:F5:83:63:2C:C8:D8:23:5C:20:C0:9C:6B:C4`. The expected self-signed certificate-chain warnings are not signature failure; CI's `apksigner verify` passed v3.
- Compared Build42 APK entry paths against Build61 baseline: 286 entries each; **zero missing non-signature entries and zero added non-signature entries**. All 283 non-signature entry paths preserved.
- Three common entry hashes changed as expected from code/build changes: `classes5.dex`, `classes9.dex`, and `lib/arm64-v8a/libvine_helper.so`. All 22 ARM64 native libraries are present. The original `assets/nestbox/original/classes14.dex` is byte-identical to Build61's preserved original DEX asset.
- The initial comparison mistakenly checked the runtime filtered `classes14.dex` against the original DEX asset; it was not byte-identical, as expected after duplicate class filtering. The corrected comparison used the preservation asset `assets/nestbox/original/classes14.dex` and passed.
- APK is built and verified, but **not yet device-runtime verified**. The remaining proof is a boot log from a test device. The separate `vold` shutdown/FUSE exception remains a secondary cleanup issue and is not claimed fixed in this APK.


## Step 4 — 2026-11-18: X11-test3 regression analysis and correction
- User test archive `X11-test3.zip` received. Host/guest details remain the same as test2 (Android 13 host, ARM64, no host AArch32; Android 11 Waydroid guest).
- **Main failure unchanged:** `bpfloader` exits status 2 and init reboots with `reboot,bpfloader-failed` (kmsg lines 529–559). The APK's prepare diagnostic says: `NestBox boot repair: bpfloader.rc has no reboot_on_failure option to remove`.
- Root cause in our patch script found: the parser compared the trimmed option to the literal string `reboot_on_failure`, but Android's rc option includes arguments (`reboot_on_failure reboot,bpfloader-failed`). Therefore it did not match and did not modify the file. This was a repair implementation bug; previous statement that it removed the fatal policy was incorrect. **The zygote part did take effect:** kmsg still reports the original import but the service `zygote_secondary` is now missing, so init's start request fails with “service zygote_secondary not found”; no `app_process32` exec failure appears in test3.
- Corrected patch on the repair branch: recognize the init option by prefix `reboot_on_failure ` and remove the full directive line only within the bpfloader service stanza. This leaves the bpfloader service itself and its trigger intact. Next build will test that the patch is actually applied (prepare.log must not show the no-option warning).
- `vold` continues to crash repeatedly in `AbortFuseConnections()` due `Permission denied [/sys/fs/fuse/connections]`; this is secondary shutdown noise but will be tracked as a separate rootless compatibility defect.
- Test3 artifact does **not** validate boot success. This build is withdrawn as a successful fix claim; its failure is documented, and the next APK must pass CI plus another device test.


## Step 5 — 2026-11-18: corrected APK build #45
- Commit `29b3c8b66e36513b5cdde8f5cb5e856f4681300d` corrected the parser to match the complete option prefix `reboot_on_failure ` rather than an exact word. Build #45 includes this correction.
- Workflow run `44285392626` completed successfully (run #45). Native helper compilation, all required native library checks, Gradle APK build, original APK restoration/merge, v3 signing, verification, and artifact upload passed.
- Artifact ID: `14418759151`; extracted APK size 79,698,460 bytes; SHA-256 `2450c3e57bee3cd3877ce0a7366c175d34256eae4232923f4232c82f1d33a9ed`.
- CI `apksigner verify`: v3 true, one signer; permanent release-certificate fingerprint check passed. 16 required native libraries passed CI; local ZIP extraction shows 22 ARM64 `.so` entries.
- Build #45 compared locally against downloaded Build61 baseline: 286 APK entries both; no missing entries and no added entries. Exactly 3 non-signature payload entries changed: `classes5.dex`, `classes9.dex`, and `lib/arm64-v8a/libvine_helper.so`; original preserved `assets/nestbox/original/classes14.dex` remains byte-identical.
- Local `jarsigner -verify` exited 0, but its output warns that Android APK entries are not fully represented in JarInputStream verification; therefore Android v3 signature validation is credited to CI's `apksigner`, not local jarsigner.
- Build #45 is the corrected APK candidate, **runtime not yet confirmed**. Test3 failure remains the last device evidence; test4 should specifically check that prepare.log no longer reports `bpfloader.rc has no reboot_on_failure option to remove`, then capture boot state/logs and any new failure.
