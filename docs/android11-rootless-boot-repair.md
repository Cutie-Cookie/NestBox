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


## Step 6 — 2026-11-18: X11-test4 advances boot to graphics startup, but SurfaceFlinger loops
- User reports Test4 remained at “Starting” for a couple minutes, then was manually shut down. No explicit UI error was displayed; RAM use rose to about 0.4 GB compared with roughly 0.1 GB in prior tests.
- Archive X11-test4.zip inspected. BPF fatal reboot is no longer the dominant observed blocker; system_server starts and enters boot_progress_system_run.
- **New main blocker:** SurfaceFlinger and vendor composer repeatedly abort. Crash message: couldn't find an OpenGL ES implementation, make sure you set ro.hardware.egl or ro.board.platform. SurfaceFlinger cannot register/start, and system_server loops waiting for the SurfaceFlinger service. This is the current boot-stall cause indicated by the logs.
- Additional repetitive crashes: Clearkey DRM factory cannot register its HAL service (registerAsService("clearkey") fails). Track separately; don't disable unrelated components.
- Device archive has repeated tombstones from restart loops. Test4 is not a successful boot.
- User requests Xiaomi setup check Background process limit be checked by default because their phone's setting is already changed. Changed SetupScreen.kt comment and AppViewModel.refreshSetup() to report this check satisfied by default, so setup no longer asks for Wireless Debugging pairing to change the limit. The rest of the setup checks remain unchanged.
- Next investigation: determine how this rootless graphics stack selects EGL/GLES libraries and what properties/host bridge are required; inspect the Android 13 guest's graphics vendor files and rootless runtime environment before applying a targeted graphics fix. Do not remove native graphics libraries or disable SurfaceFlinger to bypass the crash.


## Step 7 — 2026-11-18: Test4 graphics crash analysis and software EGL fallback
- Re-read the actual Test4 archive. It confirms the boot stall is not just an inference: SurfaceFlinger aborts with `couldn't find an OpenGL ES implementation, make sure you set ro.hardware.egl or ro.board.platform`; HWC starts on Wayland but its EGL thread also hits the loader abort. Zygote repeatedly restarts while system_server waits for SurfaceFlinger. This is the immediate blocker.
- Host graphics is reported as Mali/T606, but guest startup does not have an EGL implementation selected. Rootless mode must not assume the host GPU's vendor EGL libraries are present in the guest.
- External Waydroid documented fallback properties for unsupported/VM graphics: `ro.hardware.gralloc=default` and `ro.hardware.egl=swiftshader`. Implemented those in the NestBox guest overlay plus `ro.opengles.version=196608` (OpenGL ES 3.0) as the software-renderer capability, retaining Waydroid composer/HWC and all native components. No graphics service was removed.
- This is a targeted, evidence-driven configuration change; the software renderer's presence and runtime success still need CI/ROM inspection and device validation. If EGL continues aborting, capture which `libEGL_*` and GLES driver files are in the guest image and test a fallback only after verifying the actual library availability.
- Reference: official Waydroid docs describe SwiftShader fallback for unsupported graphics/VM environments. https://docs.waydro.id/faq/get-waydroid-to-work-through-a-vm


## Step 8 — Build #51 APK verification (2026-11-18)
- Workflow run 44292432350 completed successfully at commit `9e9631940ed935d41cc9f7eb4d64aabfa274433a`.
- Artifact ID `14421778736` (`NestBox-arm64-v8a-debug-complete`) downloaded; APK extracted locally to `NestBox-Fixed52.apk`.
- SHA-256: `c12f5a4a01b540c997a48e5c8774133055afa18a83448e6035fea51eebc399e`.
- Workflow verification step passed: apksigner verify, permanent release-key fingerprint check, package name/sdk check, ARM64-only native library check, and all 16 required libraries present. Workflow restores original APK-only components and signs after merge.
- Local ZIP test passed. Local comparison against Build61: 286 entries each, no missing or added entries; exactly 3 payload entries differ (`classes3.dex`, `classes5.dex`, `lib/arm64-v8a/libvine_helper.so`). This includes the original APK restoration/merge flow; original assets/native/DEX payload preservation is maintained.
- Runtime boot is not yet verified. This is the next device-test candidate, not a claim that graphics initialization or Android boot is fixed.


## Step 9 — 2026-11-18: Test5 indicates graphics properties were likely written to the wrong product path
- Test5 still shows the EGL loader fatal abort, with no preceding `Failed to load drivers from property ...` message in captured logcat. This suggests (not conclusively proves) that the graphics suffix property may not be loaded at boot.
- Rechecked Android 13 AOSP init property-loading source: canonical partition build properties load from `/product/etc/build.prop`. The rootless overlay incorrectly wrote to `rootfs/system/product/etc/build.prop`, which is not guaranteed to be the mounted product partition path on modern split-partition images.
- Corrected `scripts/patch_helper.py` to write to `rootfs/product/etc/build.prop` and create the correct directory. Kept the legacy `/system/product/etc/build.prop` path in the 64-bit property-rewrite list and added `/product/etc/build.prop` for compatibility. Added an explicit read-back check for `ro.hardware.egl=swiftshader` plus a diagnostic log so future captures can confirm overlay application.
- Kotlin `GuestProps.apply()` was already using the canonical `/product/etc/build.prop` target.
- This repair addresses a likely reason the prior SwiftShader property was ignored; it does **not** add SwiftShader driver binaries. Runtime test must confirm the property is loaded and whether the guest image has the matching driver libraries.
- Research sources: Android 13 init loads partition properties from `/product/etc/build.prop` (https://android.googlesource.com/platform/system/core/+/refs/tags/android-13.0.0_r27/init/property_service.cpp); EGL loader searches driver libraries based on `ro.hardware.egl` and `ro.board.platform` (https://android.googlesource.com/platform/frameworks/native/+/master/opengl/libs/EGL/Loader.cpp); Waydroid's software graphics configuration is documented as `ro.hardware.gralloc=default` and `ro.hardware.egl=swiftshader` (https://docs.waydro.id/faq/get-waydroid-to-work-through-a-vm).
- Build #55 completed successfully with the full restore/merge/sign workflow. APK SHA-256: `e03d6deca666beb64881b7bd69b1a950c7c489edc0235bfe09c6f0b185ef0930`. Locally checked: 286 entries, no missing/added entries compared with Build61; 6 changed entries are signature files, two DEX files, and `libvine_helper.so`. CI verification confirms signature and required ARM64 libraries.
- Device boot is still unverified; this is the next candidate for Test6.



## Step 10 — Test6 regression and correction (2026-11-19)
- Test6 failed during rootfs preparation, before Android init or graphics startup. The exact error was: `could not write .../rootless/rootfs/product/etc/build.prop`. The guest log shows system.img extraction completed, then the rootless engine failed while applying the NestBox overlay. There is no guest logcat or kmsg because Android never booted.
- Root cause: Step 9 changed the overlay destination to `R + "/product/etc/build.prop"` and unconditionally created `R + "/product/etc"`. This assumed a split-partition rootfs layout. The tested Android 11 system-as-root image uses the extracted path `R + "/system/product/etc/build.prop"`; creating a separate `/product` tree was incorrect and the write failed.
- Correction in commit `4f5a755ce1d99fff4047bd455484336ae1d0388b`: select the existing `/system/product/etc/build.prop` first; use `/product/etc/build.prop` only if that file already exists. If neither exists, fail with an explicit diagnostic. Do not create a new product directory. Preserve the marked overlay block and read-back verification.
- This correction restores the original extracted-image path while retaining compatibility with an already-present split-product path. It does not claim to fix EGL; the graphics driver loading problem remains to be tested after rootfs preparation succeeds.
- Build and APK verification are pending. Fixed53 is explicitly rejected as a regression and must not be used.


## Step 11 — Test7 absolute-symlink escape (2026-11-19)
- Test7 repeats the exact Test6 failure: rootfs preparation stops while writing `.../rootless/rootfs/product/etc/build.prop`; guest logcat says the instance is not running and kmsg is empty. The guest never starts.
- The previous Step 10 correction was incomplete. It used `is_regular_file(R + "/product/etc/build.prop")` as a fallback. That check follows symlinks. In this system-as-root image, `R/product` is an absolute symlink to `/system/product`; resolving it from the host process escapes the extracted rootfs and addresses the phone's own read-only `/system/product`. The write therefore fails. This explains why Fixed58 still emitted the host-side `rootfs/product/etc/build.prop` error.
- Corrected in commit `1d20084ca7acc1f76b3ca8c4ad56c219890d4384`: all host-side edits now target only `R/system/product/etc/build.prop`, and the code verifies that the extracted directory exists before writing. The unsafe `/product/etc/build.prop` fallback was removed from both the overlay and 32-bit ABI sanitation path. This keeps every host write inside the extracted rootfs.
- Fixed58 is rejected for device testing. The new build must pass rootfs preparation before another graphics/boot diagnosis is meaningful. Build and complete APK verification are pending.


## Step 12 — Test8 EGL backend override (2026-11-19)
- Test8 confirms the Test7 rootfs path correction worked: the rootless engine completed image extraction, wrote and read back the graphics overlay at `rootfs/system/product/etc/build.prop`, started Android init, and launched zygote and the Waydroid composer.
- The fatal boot loop is now specifically graphics. Guest logcat repeatedly reports `libEGL: couldn't find an OpenGL ES implementation`; both `hwcomposer.waydroid.so` and `surfaceflinger` abort in `libEGL.so`'s driver loader. SurfaceFlinger death restarts zygote, so Android never reaches boot-completed. The DRM clearkey VINTF registration crash is separate and not the display blocker.
- Root cause in NestBox: `GuestProps.writeOverlay()` appended product-level overrides `ro.hardware.egl=swiftshader`, `ro.hardware.gralloc=default`, and GLES 3.0. Product properties load after the helper's `/vendor/waydroid.prop`, so they replaced the rootless helper's graphics backend configuration. The helper intentionally configures ANGLE + gfxstream + vine gralloc for GPU mode, or ANGLE + lavapipe + default gralloc for CPU mode. The SwiftShader override did not supply SwiftShader driver binaries and also disabled the helper's vine-gralloc path.
- Corrected in commit `074d942ec39405209dbdc7fe9d0ef2e70ecb4292`: removed the three forced graphics properties from the product overlay. NestBox still applies low-memory, ROM, and spoof properties, but leaves EGL, gralloc, Vulkan, and GLES version to the rootless helper that knows which graphics backend it started.
- Test9 must confirm the guest now loads the selected ANGLE implementation and that SurfaceFlinger reaches boot completion. This source correction is not yet a verified boot fix until that device test passes.


## Step 13 — Test9 EGL driver staging and AEmulator-Plus research (2026-11-19)
- Test9 still reaches Android init and starts zygote, Waydroid hwcomposer, and SurfaceFlinger, but SurfaceFlinger and hwcomposer repeatedly abort in `libEGL.so` with `couldn't find an OpenGL ES implementation`. The rootfs path fix remains effective; this is still a guest EGL driver-discovery failure.
- NestBox's pinned Wayondroid rootless helper writes `ro.hardware.egl=angle` into `/vendor/waydroid.prop`, but its rootfs preparation does not stage any guest-side EGL/GLES driver libraries. The APK's 16 verified ARM64 JNI libraries are host-side runtime/helper libraries; they are not Android guest EGL drivers.
- Research of [AEmulator-Plus](https://github.com/somerandomusernam2/AEmulator-Plus) shows Android 11 (API 30) is handled by a dedicated `Kernel64.A11` profile. It specifies `vendor/lib64/egl` as the guest driver directory, supplies a per-API graphics/vendor layer plus a shared SwiftShader layer, and only selects its custom `aemu` bridge after the bridge is installed and running. Its `TreeFixer` maps engine EGL assets from `system/lib64/egl` into the vendor EGL directory. This is a useful architectural reference, not a drop-in engine: AEmulator-Plus uses its own native ARM64 engine and custom host/guest GL bridge.
- AEmulator-Plus is GPL-3.0. NestBox will not copy its source or proprietary/unclear-provenance assets. We will independently adapt the general driver-staging principle to NestBox's existing Wayondroid + ANGLE/gfxstream stack.
- New NestBox patch commit `c06b669f4a7195143f1a973cb17f6ed4b4db5dd1` stages only ARM64 ELF EGL/GLES libraries found under the guest's `/system/lib64/egl` and `/system/lib64` into `/vendor/lib64/egl`, only when the vendor destination is absent. Existing vendor drivers win. It refuses a symlinked vendor root and does not follow source-directory symlinks, avoiding a repeat of the Test7 host-path escape.
- The next build is a diagnostic/fix candidate, not yet a confirmed boot fix. Its rootfs-preparation log must show which drivers were staged and the resulting vendor EGL inventory. Test10 must then confirm that `libEGL` loads the selected driver and SurfaceFlinger remains alive.
