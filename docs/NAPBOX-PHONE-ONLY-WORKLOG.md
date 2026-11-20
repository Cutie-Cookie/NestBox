# NapBox phone-only compatibility worklog

Append every meaningful action, build attempt, failure, correction, and verification here. Never delete failed attempts or rewrite history to make a later result look cleaner. Include commit SHA, workflow run ID, artifact ID, exact error, evidence, and next step whenever available.

## Current state — 2026-11-20

- Active branch: `phone-only/build61-baseline`.
- Recorded branch head: `3bf939333e7ae646a9046ad4901529995ff69910`.
- Scope: built-in Android 13 Google-services ROM on Itel P55 (itel A666L), Unisoc T606 / UMS9230, Mali-G57. No Android 11/12 or other-ROM work unless the user asks.
- Last known complete baseline: Build 61, successful [workflow run #61](https://github.com/Cutie-Cookie/NestBox/actions/runs/44104470104), source commit `453f5cfb7d8c16e611742051200d93d3b5b9855e`, artifact ID `14337937391`.
- Latest branch build attempt known at this point: workflow run `44727745088`; Gradle/native compilation progressed, but original APK restoration failed because the configured GitHub release download URL returned HTTP 404. This is not permission to skip the merge.
- The full restoration script `scripts/merge_original_apk.py` pins the original APK SHA-256 to `50049680418b072934360af4116c01b5a194af6a90459fd21cdb26b3b68cfa05`. Any recovered input must match this exact hash before the script can use it.
- A Build 61 artifact is available from run #61; its successful log proves the baseline packaging path works. It is a finished APK, not automatically a substitute for the separate original APK input required by the merge script. Do not feed a merged Build 61 APK into the merge script unless it is proven to be the exact original APK by hash.
- Latest recorded branding/icon commit: `3bf939333e7ae646a9046ad4901529995ff69910` — moved the uploaded cat PNG blob to `app/src/main/res/mipmap-nodpi/ic_launcher.png`, added an adaptive icon XML, set launcher background color to `#000000`, and removed the root-level uploaded PNG.
- App ID is `app.napbox`; Kotlin namespace intentionally remains `app.nestbox`. Display name is NapBox; versionName is 0.9.0.
- UI token palette is mostly grayscale but still has `#101010` backgrounds. Adaptive icon currently has no monochrome themed-icon layer. Launcher rendering and full UI palette are not yet device-verified.
- Signing workflow currently references `NAPBOX_KEYSTORE_BASE64` and `NAPBOX_KEYSTORE_PASSWORD`, while permanent project convention requires existing `NESTBOX_KEYSTORE_BASE64` and `NESTBOX_KEYSTORE_PASSWORD`. Reconcile workflow names without asking the user to create renamed secrets. Never expose secret values in this file.
- New key certificate fingerprint expected: `77:C7:A2:52:99:2B:66:AE:F7:4D:53:A8:BF:BC:49:C2:86:40:2F:5D:08:78:B5:EF:D7:1F:60:FB:25:99:DD:A0`. Key alias: `napbox-release`. Do not record its password or Base64 here.

## Baseline verification — Build 61

Workflow run: [#61](https://github.com/Cutie-Cookie/NestBox/actions/runs/44104470104)  
Commit: `453f5cfb7d8c16e611742051200d93d3b5b9855e`  
Artifact: `NestBox-arm64-v8a-debug-complete`, ID `14337937391`.

Observed successful job steps:
- Required native library checks passed.
- Gradle debug APK build passed.
- Original APK restoration and merge passed.
- Original APK archive contained 281 entries.
- 131 original-only entries were added; 149 collisions retained the current-build entries.
- Original `classes14.dex` had 2,236 unique classes retained and 5,084 duplicate class definitions removed from runtime DEX.
- Byte-for-byte original DEX backup retained at `assets/nestbox/original/classes14.dex`.
- Required ARM64 native library checks passed.
- APK Signature Scheme v3 verification passed.
- Complete APK artifact uploaded; APK size reported as 77 MB.

This establishes Build 61 as the reference packaging process. It does not establish NapBox branch compatibility on the user's phone.

## Branding and launcher icon — commit 3bf9393

Changes observed in the branch tree:
- `applicationId` changed to `app.napbox`; `namespace` remains `app.nestbox`.
- Display name changed to NapBox.
- Version name changed to 0.9.0.
- UI token colors were shifted toward grayscale.
- Original user-uploaded cat PNG was placed at `app/src/main/res/mipmap-nodpi/ic_launcher.png`.
- Adaptive icon XML uses `@color/nb_bg` as background and `@mipmap/ic_launcher` as foreground.
- `nb_bg` is exactly `#000000`.
- Root-level upload was removed from the branch tree.

Not yet verified:
- No successful full APK build on this branch after the icon change.
- No Android 13 home-screen test or adaptive-mask crop test.
- No monochrome themed-icon layer in adaptive icon XML.
- No complete audit proving every app screen uses only black/white/grey.
- No check yet that the old release icon fallback is correct on non-adaptive launchers.

## Failed build record — run 44727745088

- Branch build was triggered by a push to the active phone-only branch.
- Native/Gradle build stages progressed successfully.
- Full APK restoration step attempted to download `NapBox-0.4.0-debug.apk` from the old upstream release URL.
- That URL returned HTTP 404.
- Build did not complete the full restore/merge/sign/verification path. Do not call this a completed APK.
- Next action: recover the exact original APK whose SHA-256 matches the pinned value in `scripts/merge_original_apk.py`. Search repository history, retained workflow artifacts, and project-owned release assets. Do not substitute the final Build 61 merged artifact unless its hash is exactly the pinned original APK hash.

## Next actions

1. Resolve the original APK input from a trusted source and verify its exact pinned SHA-256.
2. Reconcile signing workflow to the existing NESTBOX secret names; verify the secret values correspond to the new NapBox certificate before expecting the fingerprint check to pass.
3. Finish launcher icon compatibility: adaptive foreground safe zone, legacy fallback if needed, and monochrome layer for themed icons; keep background exactly `#000000`.
4. Audit app theme colors and all remaining blue references; distinguish app UI background colors from launcher background.
5. Confirm ROM cache export is copy-only and preserves the built-in Android 13 GApps source for future machines.
6. Begin Android 13 device compatibility diagnosis only after the build/restore path is healthy; use fresh test archives and record each finding.


## Failed build attempt — run 44730189264 (#127)

- Commit: `7ba6eb3283701f4f386da3d48c1e5bd7fc70df5e` on `phone-only/build61-baseline`.
- Native backend build and all required native library checks passed.
- Gradle `assembleDebug` completed successfully in 3m 34s.
- Signing secrets `NAPBOX_KEYSTORE_BASE64` and `NAPBOX_KEYSTORE_PASSWORD` were present and Gradle signing configuration validated.
- Full restore step failed immediately because upstream URL `https://github.com/rifatrajbd/NapBox-An-Android-Emulator-Support-Lineage-OS/releases/download/v0.4.0/NapBox-0.4.0-debug.apk` returned HTTP 404. Signing/complete APK verification and artifact upload were skipped.
- Confirmed upstream repository release tag `v0.4.0` is no longer available (GitHub API 404).
- Downloaded Build 61 artifact ID `14337937391` from run #61 and inspected the inner APK. SHA-256: `68a137d9ea08ab71bbd788c99993007a4d763573efbda126a530cf377d0707ab`; 286 ZIP entries; contains filtered `classes14.dex`, byte-for-byte original DEX backup `assets/nestbox/original/classes14.dex`, and required original-only libraries `libOpenglRender.so`, `libloader.so`, `libtwoyi.so`.
- Updated workflow to download the retained Build 61 artifact using `gh run download` with read-only Actions permission and verify the APK SHA-256. Updated merge script to use the preserved raw DEX backup from Build 61 and exclude duplicate backup insertion while keeping the full merge/filter/verify/re-sign path.
- Commits: workflow `6d51a0657e82ef5a45a477974fa0e8e8c8a26aaf`; merge script `69b2bbd1de7172add0140941903aad40cfc1aec6`.
- Next: monitor the workflow triggered by the merge-script commit. Do not deliver until it completes and the final APK is fully verified and compared against Build 61.


## Build 61 artifact retrieval attempt — run 44731178483 (#129)

- Native backend and all required ARM64 native library checks passed; Gradle `assembleDebug` passed in 2m 43s.
- The new Build 61 artifact download step reached `gh run download` but failed because the restore-step environment did not include `GH_TOKEN` (GitHub CLI error: “To use GitHub CLI in a GitHub Actions workflow, set the GH_TOKEN environment variable”).
- Corrected the workflow so the restore step explicitly receives `${{ github.token }}` as `GH_TOKEN`. The workflow already grants `actions: read` and `contents: read`.
- The same commit's parallel documentation-triggered runs (#128, #130, #131) are not considered valid verification attempts; they use intermediate workflow/script states and must not be used as deliverables.
- Next: a new push-triggered run must prove artifact download, checksum, DEX filtering, merge, re-sign, final verification and artifact upload all succeed.


## Successful complete NapBox build — run 44731870127 (#132)

- Active branch: `phone-only/build61-baseline`; workflow head commit: `dbd82ea56e199f89f4afa6cdb57a197d75f576ea` (source and merge logic identical to current branch head; later commit only appended this worklog).
- Workflow completed successfully. Run: https://github.com/Cutie-Cookie/NestBox/actions/runs/44731870127
- Artifact: `NapBox-arm64-v8a-debug-complete`, artifact ID `14626777688`, artifact SHA-256 `bae8e4dca9d5a898795d1a1d29200cdcb4fb80dd98054f8cf112d06e88af8e3e`.
- Downloaded and independently inspected the artifact ZIP. It contains `app-debug.apk` (80,521,841 bytes); artifact ZIP is 33,596,637 bytes.
- Final APK SHA-256: `57262c2e7948a5bb2b08180cd48da842e38b4f426fc378c2bca2aeb209ec07b2`.
- Workflow verified APK Signature Scheme v3 and checked the expected NapBox certificate fingerprint (`77c7a252992b66aef74d53a8bfbc49c286402f5d0878b5efd71f60fb2599dda0`); package ID `app.napbox`; min SDK 29; all 16 required ARM64 libraries present; no unexpected non-ARM64 ABI libraries.
- Merge log: Build 61 source archive verified at 286 entries; 131 original-only entries added; 150 colliding paths kept from current build; 2,236 unique classes retained in runtime `classes14.dex`; original raw DEX backup preserved byte-for-byte; 3 old signature entries replaced by NapBox signing.
- Independent ZIP comparison against Build 61: 0 missing non-signature entries; only expected signature metadata was replaced; one new compiled launcher-cat resource added; 9 same-path entries changed (manifest, six current DEX files, patched `libvine_helper.so`, adaptive launcher XML, and `resources.arsc`). Required original-only libraries and both DEX files were present; `classes14.dex`, its original backup, and the original-only `libOpenglRender.so`, `libloader.so`, `libtwoyi.so` matched Build 61 byte-for-byte. Total ARM64 native library entries: 22.
- This verifies a complete signed APK and preservation of Build 61's non-signature archive entries. It does not prove runtime compatibility or actual home-screen icon rendering; those require the user's Android 13 phone test.
- User requested ZIP delivery rather than a direct APK link. Delivered file is the workflow artifact ZIP; it is smaller (33.6 MB) than the contained APK (80.5 MB).


## User device test and log folder branding fix — 2026-11-20

- User installed the complete NapBox ZIP build on the Itel P55 and confirmed: installs separately from NestBox; theme and launcher icon are correct; creating and booting the built-in Android 13 GApps ROM works perfectly.
- User noticed boot logs were being written to the legacy shared-storage folder `/sdcard/Nestbox/logs`.
- Updated `app/src/main/java/app/nestbox/engine/BootLogs.kt` to write to `/sdcard/NapBox/logs`; updated fallback path documentation to `Android/data/app.napbox/files/logs`.
- Commit: `d25d4ce6fae287649ce67dc0a2ec92aa8399541f` on `phone-only/build61-baseline`.
- This is a small storage-path branding fix only. The previous tested APK's runtime results remain valid for its code; the new path change requires a new build/install to verify the new location. Do not imply the new path has been phone-tested until the user checks it.
