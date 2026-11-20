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
