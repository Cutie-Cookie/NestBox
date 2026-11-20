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


## Compatibility roadmap and uploaded test-log review — 2026-11-20

- User requested that compatibility work begin before implementing the new phone-specific preset. The intended new preset is dedicated to the Itel P55 and must coexist with Battery, Balanced, and Performance; it must be based on measurements, not guessed values.
- User also wants the guest to make efficient use of the T606's full CPU topology rather than concentrating work only on performance cores. Agreed design direction: make all eight cores eligible where the engine allows, while retaining Android/Linux scheduler decisions and host thermal controls. Do not pin to big cores or force maximum CPU frequency.
- Reviewed current implementation:
  - `Catalog.kt` currently defines Battery = 2 cores / 2 GB / 30 fps, Balanced = 4 / 3 GB / 60 fps, Performance = 6 / 4 GB / 90 fps.
  - `ModernEngine.kt` sends the selected preset's value as `cpu_cores=<n>` to the native helper. Exact helper semantics still need inspection before increasing it to 8.
  - `HostInfo.kt` reports a marketing-rounded RAM amount based on `ActivityManager.MemoryInfo.totalMem` and battery temperature, but does not yet profile CPU topology, affinity/cpuset, thermal status, or available memory pressure.
  - `ProcUtil.kt` already has process-tree and PSS measurement helpers that can support guest memory profiling.
  - `GuestProps.kt` currently handles low-memory guest properties but has no phone-specific CPU policy.
- Reviewed uploaded archives `X11-test10.zip` through `X11-test14.zip`. All five describe Nestbox 0.8.0, imported ROM id `a13imp`, and report “Powered off while starting”. Their tombstones identify the guest image as LineageOS 18.1 / Android 11, despite the host phone being Android 13. In test10, SurfaceFlinger repeatedly aborts with “couldn't find an OpenGL ES implementation”; the EGL prep log initially staged zero ARM64 driver libraries. Later archives show the SwiftShader/ANGLE fallback adjustments and vendor wrapper replacement, but the imported Android 11 guest still does not reach a stable running state. These are historical imported-Android-11 diagnostics, not evidence about the active built-in Android 13 GApps target. Do not resume Android 11 work from these logs unless explicitly requested.
- The user has separately confirmed that the current NapBox build creates and boots the built-in Android 13 GApps ROM on the actual Itel P55. That remains the active baseline for new compatibility diagnosis.
- Next technical step: inspect native helper CPU handling and add read-only host/guest diagnostics for online CPU topology, frequency policies, cgroup/cpuset/affinity, available memory and guest PSS, and thermal state. Then measure the known-good Android 13 guest before changing behavior. Prioritize boot/graphics/memory reliability; tune CPU scheduling and create the P55 preset only after those measurements.
- No APK build was requested or triggered for this planning/documentation update.


## First CPU/memory backend audit and read-only diagnostics — 2026-11-20

- Active branch only: `phone-only/build61-baseline`.
- Inspected `ModernEngine.kt`: startup sends `cpu_cores=${p.cores}` and `ram_mb=${p.ramGb * 1024}` to the native helper with `--rootless`.
- Retrieved the exact upstream Wayondroid source pinned by the repository workflow: `yoro1836/wayondroid` commit `a45f80b1aaa463d199c9056bb8dda7c01be5ece7`.
- Important CPU finding: the active rootless entry point is `RootlessServer::cmd_start` in `app/src/main/cpp/helper/rootless_server.cpp`. It parses width, height, dpi, refresh, ram_mb, boot_timeout and graphics, but does not parse `cpu_cores`. The rootless `InstanceConfig` in `rootless/rootless_instance.h` has no CPU-core field. The separate non-rootless `HelperServer::cmd_start` parses `cpu_cores`, but NapBox starts the helper with `--rootless`; that parser is not the active path. Therefore the current Battery/Balanced/Performance core counts (2/4/6) are not currently enforced by this rootless backend. Do not simply change the P55 preset to 8; first collect host cpuset/affinity and guest-visible CPU evidence, then design a correct rootless implementation if needed.
- Important memory finding: rootless mode does parse `ram_mb`, but it passes this into `PrepOptions.ram_mb`; `rootless_prep.cpp` uses it to launch `vine_lmkd --budget-mb N`. The pinned `vine_lmkd.c` source describes this as an app-private-memory budget and kills cached/background guest apps when their private memory exceeds the budget or the host is low on memory. It is not a guest RAM reservation, VM hard memory cap, or physical-memory partition. Existing UI descriptions such as “2 GB cap” therefore overstate what this setting does and need a later evidence-based wording/semantics correction. Preserve existing behavior until guest memory measurements are available.
- Added read-only host diagnostics in `app/src/main/java/app/nestbox/host/HostDiagnostics.kt` (commit `3b0963755e3582ce38cece274c741ece8665ca5f`, refined in `0ce9e0656556dd3f909b329c6ddfd767374578ea`). It captures online/present/possible CPUs, per-core topology/capacity, cpufreq policy membership/governor/frequencies, process allowed CPU list, procfs memory/pressure, cgroup CPU/memory quota and usage where readable, Android available/total/threshold memory, thermal status/zones, and battery temperature. Restricted files are explicitly marked unavailable.
- Updated `ModernEngine.collectLogs` to include `host-runtime.txt`, a read-only guest snapshot (`guest-runtime.txt`: guest-visible CPU list/affinity, memory, cgroups and SurfaceFlinger renderer lines), and NapBox+guest process-tree PSS/count in `summary.txt`. Existing helper diagnostics, guest logcat and engine stderr remain included.
- Updated machine shutdown collection to save a runtime snapshot for both successful running sessions and boot failures when Save Boot Logs is enabled. This is intended to provide useful measurements from a known-good Android 13 guest without adb or root.
- Relevant code commits: `3b0963755e3582ce38cece274c741ece8665ca5f`, `72bf27e186db41ef0bd1f17d1aa516646cb429c3`, `25e8dd68cc570f16392289ba5d063ec04a398918`, `b9d1cbb10cc72556aad2409f3c466d5556487c9a`, `0ce9e0656556dd3f909b329c6ddfd767374578ea`, `4316a751e867cf42f315f90b28eb711d1e2fa00e`.
- No CPU affinity, cpuset, scheduler, frequency, or guest memory behavior has been changed. No compatibility claim is made from source inspection alone. Next: inspect the diff for correctness, run the full Build 61-preserving workflow, monitor its compile/restore/sign/verification stages, and only after the user installs the exact verified artifact collect actual Itel P55 runtime snapshots.


### Diagnostics implementation correction — 2026-11-20

- During source review before accepting a build, caught that the generated Kotlin raw shell string had an incorrectly escaped `$f` variable in its guest cgroup loop. The malformed line was corrected to Kotlin's literal-dollar expression `"${'$'}f"` and the full loop was restored. This was caught by inspection before any build was accepted; the earlier source revision must not be treated as buildable. Correction commit: `9bedbb4518af6434ab9bd6379ca47d98d2989590`.
- This correction is retained in the worklog rather than erasing the failed intermediate attempt. The latest full workflow must compile the corrected source.


### Signing secret-name reconciliation — 2026-11-20

- Corrected `.github/workflows/android11-aarch32-fix.yml` to read the established GitHub Actions secrets `NESTBOX_KEYSTORE_BASE64` and `NESTBOX_KEYSTORE_PASSWORD` in both the Gradle signing-key restore step and independent certificate verification step. The workflow no longer references `NAPBOX_KEYSTORE_*` secret names. Commit: `a8a594396293cd78d964d1e0406c59e6e847f952`.
- The earlier overlapping runs were triggered before this workflow correction and are not accepted as the final signing verification. A new full workflow run on the corrected branch head must prove that the established secrets are available and that the NapBox certificate fingerprint still matches. No secret values are recorded or exposed.


## CI failures and signing diagnosis — 2026-11-20

- Run #140, ID `44754852143`, commit `3b0963755e3582ce38cece274c741ece8665ca5f`, completed successfully. It only compiled the standalone host-diagnostics class before guest/runtime integration was added; it is not the diagnostic build to deliver.
- Runs #141–#151 did not produce a valid APK:
  - #141 `44754912490`
  - #142 `44754956744`
  - #143 `44754990484`
  - #144 `44755003992`
  - #145 `44755115806`
  - #146 `44755147172`
  - #147 `44755370182`
  - #148 `44755457769`
  - #149 `44755500295`
  - #150 `44755613147`
  - #151 `44755679127`
- These runs used intermediate source revisions. The Kotlin raw string for the guest cgroup probe was malformed in an early edit; a subsequent update also duplicated the trailing methods of `ModernEngine.kt` (the file grew from 517 to 2,215 lines). Gradle reported Kotlin syntax errors around the guest shell loop, followed by cascading unresolved references and duplicate declarations. These were caught in CI and no such artifact was accepted. The source was restored from the clean pre-diagnostics file at commit `6be1febaaba4cfe782e743946082e4057c32100c`, then the diagnostics were reapplied with single-occurrence anchor checks and verified to have one `openDisplay` and one `stop` method. Repair commit: `33ed7c448dea783b34177b3ed6b84eb822688891`.
- Run #153, ID `44756025116`, commit `286b1c0d48df38e01a311a2a9605fe6d8684c480`: native Vulkan backend, tawcroot, rootless helper, required ARM64 library checks, Gradle setup and signing-key restore all passed. `compileDebugKotlin`, Java compilation and DEX tasks passed. Packaging failed at `:app:packageDebug` with the exact error: `No key with alias 'napbox-release' found in keystore app/signing.keystore`. This proves the existing `NESTBOX_KEYSTORE_BASE64` secret decodes with its password but its keystore does not contain the required NapBox alias. It is a signing-store contents mismatch, not a source compilation failure.
- Workflow file `.github/workflows/android11-aarch32-fix.yml` now prints only the keystore alias names and public SHA-256 certificate fingerprints during the signing restore step, without printing secret values. Commit: `2a10e702b01a125b4105d4b2776c1200f8542bea`. The next full run is needed to identify the aliases/fingerprints inside the NESTBOX keystore. Do not deliver an APK or change the expected NapBox certificate based on an unverified store.
- The earlier successful Build #132 used the separate `NAPBOX_*` secret names and verified the expected NapBox certificate, but permanent project instructions require the established `NESTBOX_*` names. The workflow has been corrected to use NESTBOX names. Do not silently switch back; inspect the NESTBOX store metadata first. If it contains an old/different key, the values under the existing NESTBOX secret names need to be updated to the NapBox keystore, without creating renamed secrets. No signing secret values are written to the repository or worklog.
- Run #152, ID `44755958912`, is an overlapping build of the corrected Kotlin source before the final memory-plan documentation commit; monitor its terminal result as well. The authoritative source head after the signing metadata step is the later active branch commit.


## Confirmed NESTBOX signing-store mismatch — 2026-11-20

- Runs #154 (`44757079693`) and #155 (`44757132819`) both completed with failure at `:app:packageDebug`; no APK was produced. Both runs used the corrected source and the existing NESTBOX secret names.
- The added safe metadata output confirmed that `NESTBOX_KEYSTORE_BASE64` decodes successfully with the supplied password, but its keystore contains alias `nestbox-release` with SHA-256 certificate fingerprint `1D:D1:CF:B8:84:6E:F3:DD:B4:39:C1:C8:B2:32:F2:C4:0F:90:75:F5:83:63:2C:C8:D8:23:5C:20:C0:9C:6B:C4`. Gradle then fails because the configured required alias `napbox-release` is absent. This is an old/different signing identity, not a missing password or malformed Base64.
- The expected NapBox signing identity remains alias `napbox-release`, certificate fingerprint `77:C7:A2:52:99:2B:66:AE:F7:4D:53:A8:BF:BC:49:C2:86:40:2F:5D:08:78:B5:EF:D7:1F:60:FB:25:99:DD:A0`, verified by earlier Build #132 using the separate NAPBOX-named secret values. Do not substitute the old NESTBOX certificate, because the installed NapBox update path depends on the expected certificate.
- Updated workflow signing restore step to check the alias and SHA-256 fingerprint before Gradle packaging, so future mismatches fail early and clearly. The workflow still reads only the established NESTBOX secret names. The existing NESTBOX secret values must be replaced with the same NapBox release keystore and matching password before another trusted build; do not create renamed secrets.


### Use the existing NapBox signing secrets — 2026-11-20

- Clarified the signing-secret mismatch with the user: both secret pairs already exist. The `NAPBOX_KEYSTORE_BASE64` and `NAPBOX_KEYSTORE_PASSWORD` pair was used by successful Build #132 and contains the required NapBox release identity. The separate `NESTBOX_*` pair contains the old NestBox certificate and is not suitable for NapBox.
- Updated the project decision to use the already-present `NAPBOX_*` secrets directly in the workflow. No secret values are copied, renamed, recreated, or exposed, and no user-side GitHub settings change is required.
- Workflow change updates both signing-key restore and final APK re-sign steps to read `NAPBOX_*`, while retaining the preflight alias/fingerprint check, Build 61 restoration/merge, zipalign, apksigner and final certificate verification. This is a secret-name wiring correction only; it does not change the signing identity or simplify the Build 61 process.


- Change record commits: plan update `d115ca188dbd8a57598f26b42f8ff6361334e18c`; worklog decision `6e9639f3325e9d78641f215ba53b6c603737ade4`; workflow wiring `0cceee0836b72db11c473eb9756c151e003413bd`. All changes were made only on `phone-only/build61-baseline`.
- Post-update verification: fetched the workflow from the active branch and confirmed both signing stages reference `secrets.NAPBOX_KEYSTORE_BASE64` and `secrets.NAPBOX_KEYSTORE_PASSWORD`; no `secrets.NESTBOX_*` references remain in the workflow. The combined commit-status query returned no status entries at the time of checking, and the available commit-run lookup returned no runs (that endpoint only reports pull-request-triggered runs). Therefore this records a verified workflow edit, not a successful new build. Build 61's restoration, merge, alignment, signing and final verification stages remain intact.


## Signing correction, successful diagnostic APK, and Build 61 comparison — 2026-11-20

- The user clarified that both GitHub secret pairs already exist and that the `NAPBOX_*` pair is the known-good NapBox signing identity from Build #132. Updated the workflow to use `NAPBOX_KEYSTORE_BASE64` and `NAPBOX_KEYSTORE_PASSWORD` directly. No user-side secret edits or new keys were needed.
- Failed workflow runs after the previous checkpoint:
  - #156, ID `44758345693`, commit `30b70ec0c1cca71249cb3034d6bdf63157ac2987`: stopped at signing preflight because it still used the old NESTBOX secret pair; the decoded store had alias `nestbox-release`, not `napbox-release`.
  - #157, ID `44760056489`, commit `d115ca188dbd8a57598f26b42f8ff6361334e18c`: same old NESTBOX secret-name wiring and same alias mismatch.
  - #158, ID `44760063704`, commit `6e9639f3325e9d78641f215ba53b6c603737ade4`: same old NESTBOX secret-name wiring and same alias mismatch.
  These are obsolete wiring failures, not failures of the corrected workflow or diagnostics source.
- Successful full Build 61-based runs:
  - #159, ID `44760074429`, commit `0cceee0836b72db11c473eb9756c151e003413bd`, artifact ID `14640738488`.
  - #160, ID `44760138294`, commit `31e913d72bf360294729858ae34bc166a2928892`, artifact ID `14641915375`. This is the selected latest artifact.
- Run #160 completed every workflow step successfully: native runtime fetch/build, gfxstream Vulkan backend, tawcroot, rootless helper, all required ARM64 library prechecks, NapBox signing-store preflight, Gradle Kotlin/Java/DEX/package tasks, Build 61 original APK restoration and DEX merge, zipalign, APK re-signing, final signature/package/native-library checks, and artifact upload.
- Run #160 signing preflight printed alias `napbox-release` and SHA-256 certificate fingerprint `77:C7:A2:52:99:2B:66:AE:F7:4D:53:A8:BF:BC:49:C2:86:40:2F:5D:08:78:B5:EF:D7:1F:60:FB:25:99:DD:A0`. Final `apksigner verify` passed with v3 signature; the workflow's certificate fingerprint grep passed. Package check confirmed `app.napbox` and minimum SDK 29.
- Run #160 merge log: Build 61 source APK checksum matched expected `68a137d9ea08ab71bbd788c99993007a4d763573efbda126a530cf377d0707ab`; source archive contained 286 entries; 131 original-only paths were restored; 150 colliding paths retained current-build versions; 2,236 unique classes from original `classes14.dex` were retained; original DEX backup remained preserved byte-for-byte; obsolete original signing entries were removed for re-signing. All original non-signature entry paths were verified by the workflow.
- Independently downloaded and inspected the exact run #160 artifact and Build 61 reference artifact. Build 61 had 286 ZIP entries; run #160 has 287. There are no missing non-signature Build 61 entries. The only removed paths are the two old `META-INF/NESTBOX-*.RSA/.SF` signature files; the new `META-INF/NAPBOX-R.RSA/.SF` files replace them. The only new non-signature path is the intended `res/mipmap-nodpi-v4/ic_launcher_cat.png`. The 11 changed paths are the current manifest/signing manifest, current-build DEX files (`classes2.dex`–`classes5.dex`, `classes7.dex`, `classes11.dex`), updated `libvine_helper.so`, adaptive launcher XML, and resources table. No unexpected missing original assets or native-library paths were found.
- Independent byte comparison confirmed `assets/nestbox/original/classes14.dex` is byte-identical to Build 61 and runtime `classes14.dex` is also byte-identical. The final APK contains 22 ARM64 native libraries, including all 16 required libraries; CI verified every required library as AArch64 and confirmed no non-ARM64 native ABI libraries were packaged.
- Selected APK: 80,542,321 bytes; SHA-256 `f2f3275699f529db67bd0d91a437e374753564bdb61f0a8065a5fba9afbc740d`.
- Artifact ZIP: artifact ID `14641915375`, 33,604,011 bytes; SHA-256 `36453d5cf43bf266a950fb8a9c5389985edf6062a299795154459a4276ff83d9`. GitHub artifact URL: `https://github.com/Cutie-Cookie/NestBox/actions/runs/44760138294/artifacts/14641915375`.
- This is a verified complete diagnostic APK ready for the next Itel P55 device test. It does not yet prove that the new host/guest diagnostic snapshots collect correctly at runtime; that must be confirmed on the phone. Do not claim further compatibility based solely on CI.


## First uploaded Itel P55 runtime diagnostics — 2026-11-20

- User uploaded Phone-test1.zip after using the diagnostic Build #160 for a while. Archive contains summary.txt, host-runtime.txt, guest-runtime.txt, diag.txt, guest logcat, kernel log and engine logs for Machine 1.
- Session identity: NapBox 0.9.0; Machine 1, modern engine, built-in Android 13 guest (a13imp), Performance preset (perf), 720×1600 at 90 Hz, GPU acceleration true. Snapshot reason: user stopped running machine. Engine state in diagnostics: running, booted. Guest logcat records sys.boot_completed=1.
- CPU measurements: host online/present/possible 0-7; NapBox process Cpus_allowed_list: 0-7; guest online and allowed CPU lists 0-7. Per-core capacity: CPUs 0–5 = 544, CPUs 6–7 = 1024. cpufreq policy0 (CPUs 0–5) uses schedutil, current 614400 Hz, max 1612000 Hz; policy6 (CPUs 6–7) uses schedutil, current 1612000 Hz, max 1612000 Hz. This confirms all eight CPUs are eligible/visible in this run, but does not prove the native rootless helper enforces the CPU preset. No affinity/frequency changes are warranted from one snapshot.
- Memory: ActivityManager total 8,149,807,104 bytes; available 1,826,951,168 bytes; threshold 226,492,416 bytes; lowMemory=false. /proc/meminfo: MemTotal 7,958,796 kB; MemAvailable 1,530,560 kB; SwapTotal 4,377,332 kB; SwapFree 1,310,864 kB. NapBox+guest process tree is 117 processes and summed PSS 2,126,692,352 bytes (~1.98 GiB). These are one-time readings at stop, not peak values.
- Important interpretation: guest MemTotal/MemAvailable and swap values are effectively identical to host values, and guest cgroup paths mirror the host app cgroup paths. The rootless environment exposes bound host proc/cgroup views. Do not treat guest meminfo as independent guest RAM or infer a hard guest RAM allocation/cap from it. Swap usage is substantial; collect another representative snapshot before increasing any budget or adding a P55 preset.
- Thermal: Android thermal status 0 (none); battery temperature 37.2°C at snapshot. This is a single point, not a sustained thermal test.
- Graphics: guest reports ANGLE, Vulkan 1.3.0, Virtio-GPU GFXStream (Mali-G57), gfxstream 25.3.6, OpenGL ES 3.1. Wayland reports 720×1600 at 90 Hz and a connected client. Guest boot reports GPU gfxstream and rootless su. It also prints low memory mode on; source/trigger for this state remains to be traced.
- Guest logcat contains no FATAL EXCEPTION, fatal signal, ANR, or OutOfMemoryError. It contains 2,041 Fence error lines, predominantly sync_merge(...) returning Inappropriate ioctl for device (-25), plus some sync_file_info returned NULL. ANGLE/Vulkan nevertheless initialized and the guest stayed booted. This is a graphics synchronization warning that may matter if the user observed flicker/stutter, but is not by itself proof of rendering failure. Other permission-denied/missing host-kernel-interface messages are present in the rootless guest.
- No code or runtime settings were changed from this snapshot. Next action: correlate fence warnings with the user's actual experience; if tuning is needed, collect a longer representative run and compare available memory, PSS, swap, thermal status, and observed behavior. Never infer guest RAM from the bound host procfs values.


## User-reported low-FPS symptom and source audit — 2026-11-20

- User reports noticeable lag / low FPS inside the Android guest. Host phone UI remains smooth (user describes it as roughly 10x smoother); no flickering, freezes, or unusual heating.
- Correlates with first snapshot: Performance preset, 720×1600, 90 FPS target, GPU acceleration enabled; ANGLE/Vulkan via gfxstream/Mali-G57 active. 2,041 guest fence/sync warnings were present, but there were no fatal exceptions, ANRs, OOM events, visible flicker, or freezes. Do not treat these warnings as a confirmed rendering failure.
- Source audit: Catalog.kt Performance preset is 6 cores / 4 GB / 90 FPS; ModernEngine.start() passes cpu_cores=6, ram_mb=4096, and refresh=90 to the helper. Previously established rootless helper does not consume cpu_cores; all 8 host CPUs remain eligible. ram_mb is the lmkd budget, not a hard guest RAM reservation/cap. VineRuntime.setDisplayFrameRate() is called with preset FPS. The guest's reported ANGLE/Vulkan renderer proves backend initialization, not achieved FPS.
- AppSettings.lowMemory defaults true. GuestProps.LOW_MEMORY sets ro.config.low_ram=true, smaller Dalvik heap start/growth/maximum, two dex2oat threads and lower background process allowance. Runtime commands cap cached processes at 8. These settings could contribute to app-level GC/cache churn for some workloads, but this is only a hypothesis; do not disable it without a controlled A/B test due to observed host memory/swap headroom.
- ModernEngine.health() currently emits fps=-1; actual frame rate is not measured. Current runtime snapshot also lacks SurfaceFlinger frame timestamps and GPU devfreq/busy readings. This is the next instrumentation gap to address using read-only probes.
- No source/runtime tuning change made. Proposed next step: add best-effort read-only SurfaceFlinger frame timing and host GPU devfreq/busy probes, plus CPU/process counters if permitted, then compare on-device. An optional controlled user A/B is Performance 90 FPS vs Balanced 60 FPS at identical 720×1600 workload; do not change Low memory mode at the same time.
- Documentation-only CI builds triggered by the diagnostic record completed successfully:
  - #162, run ID 44764925030, commit 8fc599d672eece90959e428d58c5fb50e8fb04ae.
  - #163, run ID 44764931751, commit 2f24f489561a299992153f6122d3a5e26f4ab0a5.
  Both full jobs ended with success, including final complete installable ARM64 APK verification and artifact upload. No new APK is being selected or delivered from these documentation-only runs.


## Low-FPS telemetry instrumentation attempt — 2026-11-20

- Based on the user's report of guest-only low FPS with a smooth/cool host phone and no visible graphics corruption, added read-only guest frame telemetry to app/src/main/java/app/nestbox/engine/modern/ModernEngine.kt:
  - SurfaceFlinger layer list (first 40 lines)
  - SurfaceFlinger --latency output (last 130 lines)
  - gfxinfo summary (first 180 lines)
- Added best-effort Mali/GPU devfreq probing to app/src/main/java/app/nestbox/host/HostDiagnostics.kt for matching GPU/Mali/3D nodes: current/min/max frequency, available frequencies, governor, load/busy/total time and polling interval. Missing/restricted nodes are explicitly reported unavailable.
- Source commits, both on phone-only/build61-baseline:
  - ModernEngine guest frame telemetry: d706c64d38e159e29970c374a151a874d49a1c04 (workflow #166, run ID 44767118092).
  - Host GPU devfreq telemetry: c5c218105d121cceff19561202d55abb3e6d2942 (workflow #167, run ID 44767130349).
- These are measurement-only changes. No performance settings, CPU affinity, frequencies, memory budgets, refresh targets, Low memory mode, or GPU backend were altered. No claim of an FPS fix is made; the new logs are intended to identify whether the bottleneck is frame pacing, GPU saturation, or guest-side overhead.
- Full Build 61 workflow status and final artifact verification are pending; record terminal results and artifact comparison below before offering a new diagnostic APK.


## Guest-wide low-FPS confirmation, boot warnings, and telemetry build #169 — 2026-11-20

- User clarified that low FPS is noticeable across the entire Android guest, including the guest home screen and apps; the host phone UI remains smooth. This points to a guest-wide rendering/scheduling issue rather than one app-specific workload. Root cause remains unproven because the prior health API reports fps=-1 and no actual FPS measurements had been captured.
- User supplied a screenshot of the next normal boot. The visible guest init messages were:
  - `init: Unable to write -1000 to /proc/1/oom_score_adj` / permission denied.
  - `init: Failed to unmount /debug_ramdisk: Invalid argument`.
  - `selinux: Could not set context for /data: Operation not supported on transport endpoint`.
  User reports the machine subsequently booted normally with no boot failure. Treat these as non-fatal rootless-environment compatibility warnings for this observed boot, not as proof of the low-FPS cause. Do not alter rootless mounts, SELinux behavior, or init permissions without evidence; avoid destabilizing successful boot.
- Telemetry source changes are present on the active branch and the latest full Build 61 workflow #169 completed successfully:
  - run ID `44767187829`, commit `b6ff5b351ff49dd1ba1282c704894e4cdae8b99c`, branch `phone-only/build61-baseline`.
  - Workflow job ID `136394841241`, conclusion success. Build, Build 61 restoration/merge, APK verification and artifact upload all succeeded.
  - Artifact ID `14646288486`, name `NapBox-arm64-v8a-debug-complete`, ZIP SHA-256 `0d9fad3e612e34dd68277f6e70f3ada0b9007a9a68d482d8c34a0b62c6f25c0a`, size 33,605,605 bytes.
  - Inner APK SHA-256 `cbb146d0ab2f3d97df90ee8454b9818195d6663931517f5c6dd3bc073a6b21e9`, size 80,542,321 bytes. CI log reports v3 signature verification true, required NapBox certificate fingerprint check passed, package `app.napbox`, min SDK 29, and all 16 required ARM64 libraries present.
- Downloaded and independently inspected artifact ZIP and inner APK. ZIP contains exactly `app-debug.apk`. ZIP SHA-256 independently matches GitHub artifact digest. Compared inner APK against Build 61 reference APK (286 baseline entries vs 287 candidate): no missing non-signature entries; only added non-signature path is intended `res/mipmap-nodpi-v4/ic_launcher_cat.png`; 11 changed non-signature paths are `AndroidManifest.xml`, `META-INF/MANIFEST.MF`, DEX files `classes11.dex`, `classes2.dex`–`classes5.dex`, `classes7.dex`, `lib/arm64-v8a/libvine_helper.so`, adaptive launcher XML, and `resources.arsc`. These are consistent with current app/runtime changes and NapBox branding; no unexpected missing paths found.
- Independent comparison confirms both runtime `classes14.dex` and `assets/nestbox/original/classes14.dex` are byte-identical to Build 61. All 16 required ARM64 libraries are present and there are no non-ARM64 native-library paths. Workflow log confirms original archive 286 entries, 131 original-only paths restored, 150 collisions retained from current build, 2,236 unique classes retained in runtime classes14.dex, original backup preserved, and original non-signature paths verified.
- Local container did not have apksigner available for a second local certificate inspection; rely on the successful workflow's explicit `apksigner verify --print-certs` check and expected fingerprint grep. No claim of local independent certificate re-verification is made.
- Telemetry changes are observational only: SurfaceFlinger layers/latency, gfxinfo summary, and best-effort host GPU/Mali devfreq/busy counters. No performance settings, CPU affinity/frequency, memory budget, refresh target, Low memory mode, or graphics backend were changed. The artifact is ready for the next controlled device diagnostic run, not an FPS fix and not proof of runtime performance improvement.
