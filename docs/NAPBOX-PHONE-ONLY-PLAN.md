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

Do not rename these secrets. If the signing identity changes, replace the values under these same names only after explicit coordination and verify the resulting certificate fingerprint. The workflow currently needs an audit because the branch's workflow was changed to read `NAPBOX_KEYSTORE_BASE64` and `NAPBOX_KEYSTORE_PASSWORD`; that conflicts with this project's established secret names and must be reconciled before the next trusted build.

New NapBox keystore details recorded during this project:
- Alias: `napbox-release`
- Store and key password: `NapBox!P55_2026#Key`
- Certificate SHA-256: `77:C7:A2:52:99:2B:66:AE:F7:4D:53:A8:BF:BC:49:C2:86:40:2F:5D:08:78:B5:EF:D7:1F:60:FB:25:99:DD:A0`

The keystore password and Base64 are sensitive. Do not put either secret value in this repository, plan, worklog, commits, or logs. If the new key is adopted, make sure the two existing NESTBOX secrets contain the new keystore Base64 and password, then confirm the workflow's expected fingerprint matches it. A new signing certificate means users generally cannot install it as an update over an APK signed by the old certificate; warn before installation and account for app data.

## 6. Work sequence

1. Read this plan and the latest worklog.
2. Verify branch head and ensure all work is on `phone-only/build61-baseline`.
3. Audit branding, app ID, icon resources, theme colors, signing secret names/fingerprint, ROM cache/export behavior, and the complete Build 61 workflow.
4. Fix the original-APK restoration input failure without removing or simplifying `scripts/merge_original_apk.py` or its checks. The old release URL currently returns 404; locate a trustworthy copy from repository history/artifacts or another project-owned source and verify its SHA-256 equals the exact expected hash in the merge script before using it.
5. Only then begin targeted Android 13 host compatibility diagnosis, using user-provided logs and measured device behavior. Change one evidence-backed cause at a time.
6. Build with the full Build 61 workflow. Monitor the workflow until terminal status; inspect logs on failure and record the cause before retrying.
7. Download the exact successful artifact and verify its identity, signature/certificate, required native libraries, DEX structure/backups, original assets/resources, and APK entry/hash differences against Build 61.
8. Ask the user to install/test only when the APK has passed artifact checks. Do not claim runtime compatibility until device testing confirms it.

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
