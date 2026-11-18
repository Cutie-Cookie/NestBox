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

### Step 2 — pending
Source-level investigation and first targeted repair not yet applied.
