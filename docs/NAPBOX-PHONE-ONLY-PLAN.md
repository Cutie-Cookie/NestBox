# NapBox phone-only compatibility plan

**Active branch:** `phone-only/build61-baseline`  
**Repository:** `Cutie-Cookie/NestBox`  
**Current recorded branch head when this plan was written:** `3bf939333e7ae646a9046ad4901529995ff69910`  
**Baseline:** Build 61, workflow run [#61](https://github.com/Cutie-Cookie/NestBox/actions/runs/44104470104), commit `453f5cfb7d8c16e611742051200d93d3b5b9855e`.

This file is the current source of truth for scope, goals, and acceptance criteria. Read it at the start of each new work session, then read [NAPBOX-PHONE-ONLY-WORKLOG.md](NAPBOX-PHONE-ONLY-WORKLOG.md) for the latest attempt, including failed attempts and their evidence. Append to the worklog; do not erase failed history.

## 1. Scope — do not drift

Target only the user's built-in **Android 13 Google-services ROM** on the user's Itel P55 (itel A666L), Unisoc T606 / UMS9230, Mali-G57, 8 GB physical RAM.

Do not spend effort on Android 11, Android 12, generic ROM support, Xiaomi/HyperOS compatibility, or other devices unless the user explicitly changes scope. Historical Android 11 repair documents remain historical evidence only; they are not the active plan.

Primary goal: make NapBox install, launch, create a machine, and boot the built-in Android 13 GApps guest reliably on this exact phone, with graphics and rootless operation working. Do not claim compatibility until the user tests the produced APK on the phone and supplies the resulting behavior/logs.

## 2. Permanent branch and baseline rules

- Work only on `phone-only/build61-baseline`. Never edit, commit, merge, rebase, or trigger changes on any other branch.
- Build 61 is the complete reference, not a simplified build template.
- Build 61 successful reference run: [workflow run #61](https://github.com/Cutie-Cookie/NestBox/actions/runs/44104470104).
- Baseline artifact: `NestBox-arm64-v8a-debug-complete`, artifact ID `14337937391`, 77 MB APK.
- Run #61 completed successfully. Its logs report: original APK verified (281 entries), 131 original-only entries added, 149 colliding paths kept from the current build, original `classes14.dex` preserved byte-for-byte as an asset, 2,236 unique classes retained in runtime `classes14.dex`, required ARM64 native libraries verified, and APK Signature Scheme v3 verification passed.
- Preserve the full original APK restore/merge, DEX filtering/backup, native library, assets/resource, patch, packaging, zipalign/signing and verification steps. Never bypass restoration to get a green build.
- Compare every candidate APK against the Build 61 artifact. Explain every missing or changed entry.

## 3. Device profile and runtime questions

Known host device:
- Itel P55 (itel A666L)
- Unisoc T606 / UMS9230
- 2× Cortex-A75 + 6× Cortex-A55
- Mali-G57 GPU
- 8 GB physical LPDDR4X
- Android 13, built-in Google-services ROM

Investigate actual memory limits and guest allocation rather than assuming all 8 GB can be assigned to the guest. User observed that the guest appears to use about 2 GB even when Android seems to allow roughly 3–4+ GB. Measure available memory, process limits, cgroup/LMK constraints, and guest configuration before changing allocation.

Important implementation distinction discovered in the pinned rootless backend: the current `ram_mb` startup argument configures `vine_lmkd --budget-mb`, an app-private-memory budget that drives cached/background guest-app killing under budget or host memory pressure. It does not reserve guest RAM or enforce a hard guest memory cap. Do not describe the existing preset values as actual guest RAM caps; measure the guest and host first, then correct the UI semantics and choose safe P55 values.

Keep the built-in Android 13 GApps ROM available in the shared ROM cache. Export must COPY, never MOVE. Do not break future machine creation by consuming or relocating the shared ROM source.

## 4. Product identity and appearance — current work, not compatibility proof

Requested identity:
- App display name: NapBox.
- Application ID: `app.napbox`.
- Existing Kotlin namespace remains `app.nestbox` intentionally unless a deliberate full package migration is separately planned and tested.
- Monochrome white/black/grey visual direction.
- Launcher artwork: user's original sleepy white cat PNG.
- Launcher background: exactly `#000000`.

Current recorded implementation at the plan's creation:
- `applicationId = "app.napbox"`, `versionName = "0.9.0"`.
- App label is NapBox.
- `app/src/main/res/mipmap-nodpi/ic_launcher.png` contains the uploaded PNG blob (822,747 bytes).
- `app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml` points its background to `@color/nb_bg` and foreground to `@mipmap/ic_launcher`; `nb_bg` is `#000000`.
- The root-level uploaded PNG was removed from the branch when it was moved into the resource path.
- The UI design tokens are mostly grayscale, but some base surfaces remain `#101010`; this is separate from the launcher background requirement. Audit all app UI colors before claiming the entire UI is pure black/white.
- Audit legacy launcher fallback resources and Android themed-icon monochrome support. The current adaptive XML has no `<monochrome>` layer, so themed icon support is not yet verified.
- A resource commit is not proof that the icon renders correctly on the user's launcher. Check safe-zone/cropping, adaptive masks, icon density/rendering, and actual home-screen appearance on Android 13.

## 5. Signing

Use the repository's existing Actions secret names exactly:
- `NESTBOX_KEYSTORE_BASE64`
- `NESTBOX_KEYSTORE_PASSWORD`

Do not rename these secrets. If the signing identity changes, replace the values under these same names only after explicit coordination and verify the resulting certificate fingerprint. The workflow has been corrected to read the established `NESTBOX_KEYSTORE_BASE64` and `NESTBOX_KEYSTORE_PASSWORD` names. However, CI runs #154 and #155 decoded the current NESTBOX store and found alias `nestbox-release` with certificate SHA-256 `1D:D1:CF:B8:84:6E:F3:DD:B4:39:C1:C8:B2:32:F2:C4:0F:90:75:F5:83:63:2C:C8:D8:23:5C:20:C0:9C:6B:C4`, not the required NapBox alias `napbox-release` and fingerprint `77:C7:A2:52:99:2B:66:AE:F7:4D:53:A8:BF:BC:49:C2:86:40:2F:5D:08:78:B5:EF:D7:1F:60:FB:25:99:DD:A0`. Update the values under the existing NESTBOX secret names to the NapBox release keystore and matching password before another trusted build. Do not rename secrets or sign with the old certificate.

New NapBox keystore details recorded during this project:
- Alias: `napbox-release`
- Store and key password: `NapBox!P55_2026#Key`
- Certificate SHA-256: `77:C7:A2:52:99:2B:66:AE:F7:4D:53:A8:BF:BC:49:C2:86:40:2F:5D:08:78:B5:EF:D7:1F:60:FB:25:99:DD:A0`

The keystore password and Base64 are sensitive. Do not put either secret value in this repository, plan, worklog, commits, or logs. If the new key is adopted, make sure the two existing NESTBOX secrets contain the new keystore Base64 and password, then confirm the workflow's expected fingerprint matches it. A new signing certificate means users generally cannot install it as an update over an APK signed by the old certificate; warn before installation and account for app data.

## 6. Work sequence

1. Read this plan and the latest worklog.
2. Verify branch head and ensure all work is on `phone-only/build61-baseline`.
3. Audit branding, app ID, icon resources, theme colors, signing secret names/fingerprint, ROM cache/export behavior, and the complete Build 61 workflow.
4. Fix the original-APK restoration input failure without removing or simplifying `scripts/merge_original_apk.py` or its checks. RESOLVED: the workflow now retrieves the verified Build 61 artifact (run #61) and checks its SHA-256 before the complete restoration/merge process. See the worklog for evidence.
5. Only then begin targeted Android 13 host compatibility diagnosis, using user-provided logs and measured device behavior. Change one evidence-backed cause at a time.
6. Build with the full Build 61 workflow. Monitor the workflow until terminal status; inspect logs on failure and record the cause before retrying.
7. Download the exact successful artifact and verify its identity, signature/certificate, required native libraries, DEX structure/backups, original assets/resources, and APK entry/hash differences against Build 61.
8. Ask the user to install/test only when the APK has passed artifact checks. Do not claim runtime compatibility until device testing confirms it.

## 8. Itel P55 compatibility and phone-specific preset

The user wants a new preset dedicated to the Itel P55, alongside Battery, Balanced, and Performance. This is a separate phase after core compatibility is understood; do not add a preset by guessing values.

### First phase: measure before tuning

1. Establish the current known-good baseline using the built-in Android 13 Google-services ROM that the user confirmed creates and boots on the phone.
2. Audit the current engine path and its CPU semantics. Initial source inspection found that `ModernEngine` sends `cpu_cores`, but the selected `--rootless` helper path parses startup arguments in `RootlessServer::cmd_start` without reading `cpu_cores`; the rootless `InstanceConfig` has no CPU-core field. The separate non-rootless `HelperServer` parses `cpu_cores`, but that is not the path used by NapBox. Therefore the existing 2/4/6 CPU preset labels are not currently enforced by the rootless backend. Do not implement a CPU count until host cpuset/affinity and guest-visible topology are measured.
3. Collect read-only host diagnostics where Android permissions allow: online CPU list and topology, per-policy CPU frequencies/capacity, process CPU affinity and cgroup/cpuset quota, host available memory and low-memory threshold, app/guest PSS, memory cgroup limits/events, and thermal status/temperature. Missing or restricted sysfs values must be reported as unavailable, not guessed. Initial implementation adds `HostDiagnostics.snapshot()` and stores `host-runtime.txt`, guest CPU/memory/graphics details in `guest-runtime.txt`, and app+guest process-tree PSS in boot-log snapshots. Snapshots are saved on machine stop as well as boot failure when Save Boot Logs is enabled.
4. Collect guest-side diagnostics after boot: guest-visible CPU count, CPU topology/affinity if exposed, guest memory totals, service state, graphics renderer, and boot completion.
5. Change one evidence-backed compatibility issue at a time and compare against the known-good baseline.

### CPU design principle

The Itel P55's T606 is an 8-core heterogeneous SoC (2 Cortex-A75 performance cores + 6 Cortex-A55 efficiency cores). The goal is to make all eight eligible for guest work when the host scheduler and engine permit it—not to pin the guest to the two A75 cores, force maximum frequencies, or keep every core busy continuously. Android/Linux scheduling and thermal management should continue to choose where runnable work executes. Confirm what `cpu_cores` means in the native helper before setting the phone-specific preset to 8. Do not add custom affinity pinning or frequency writes unless measurements prove a specific need and the change is safe and reversible.

### Phone-specific preset

Add a dedicated Itel P55 preset only after measuring real host limits and validating the existing Android 13 guest. It should expose the most useful safe CPU capacity, choose a sustainable RAM cap rather than the phone's advertised 8 GB, and select a sensible refresh-rate target. Preserve the three existing presets unchanged. The new preset must be optional and must not override the host's thermal or memory-pressure controls.

### Compatibility order

Prioritize reliable machine creation and repeatable boot, graphics/display stability, guest memory stability, input/audio/network/storage, then CPU and frame-rate tuning. A phone-specific preset is not a substitute for fixing boot or graphics incompatibilities.

## 7. Definition of done

A fix is complete only when:
1. The targeted change is implemented.
2. Full Build 61-based workflow succeeds.
3. APK signature and expected certificate fingerprint verify.
4. Required ARM64 native libraries and all original APK-only components/DEX backups/assets are present.
5. APK contents are compared with Build 61 and all differences are explained.
6. The exact artifact from the successful workflow is identified.
7. The user tests it on the Itel P55 Android 13 GApps ROM and confirms the relevant behavior.

A successful Gradle compile or CI workflow alone is not proof of runtime compatibility.


## Restoration input update — 2026-11-20

The upstream v0.4.0 release URL used for the original APK returns HTTP 404 and the upstream release/tag is no longer available. The Build 61 complete artifact from run #61 was downloaded and inspected. Its inner APK SHA-256 is `68a137d9ea08ab71bbd788c99993007a4d763573efbda126a530cf377d0707ab`; it contains 286 entries, filtered runtime `classes14.dex`, the byte-for-byte original DEX backup at `assets/nestbox/original/classes14.dex`, and required original-only ARM64 libraries. The workflow now downloads that exact retained Build 61 artifact and verifies its SHA-256 before using it as the restoration source. The merge script preserves the raw DEX backup separately and filters the Build 61 runtime DEX against current-build classes. This is a controlled replacement of the unavailable upstream input with the verified full Build 61 reference, not a skipped merge. Final APK still must pass all merge, signing, entry, DEX, native-library and signature checks.


## First device-test feedback — 2026-11-20

The user confirmed on the Itel P55 Android 13 built-in ROM: NapBox installs separately from NestBox; theme and launcher icon look correct; creating and booting the built-in Android 13 ROM works perfectly. A minor branding issue was identified: boot logs were saved under the legacy shared-storage folder `/sdcard/Nestbox/logs`. Updated `BootLogs.kt` to use `/sdcard/NapBox/logs`; the app-private fallback is now documented as `Android/data/app.napbox/files/logs`. This is a path-only branding correction, not a compatibility fix. Device compatibility for the tested built-in ROM is confirmed by the user's test, while other machines/features still need targeted testing.
