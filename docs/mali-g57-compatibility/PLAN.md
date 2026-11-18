# Investigation and implementation plan

## Phase 0 — Establish a known baseline
1. Keep Build #61 as the candidate baseline.
2. Receive Test5 diagnostics from the same existing machine, without ROM reinstall, data wipe, or machine recreation.
3. Compare Test5 with Test4 and record changed log lines and process state.
4. Verify APK identity/signature and build commit before attributing behavior to a patch.

**Exit condition:** Test5 logs are available and classified as pass, partial progress, or same failure.

## Phase 1 — Validate the targeted gfxstream fallback
Inspect:
- Whether the R8/R16 non-external fallback log appears for VK_FORMAT_R8_UNORM.
- Whether host logs still show R8_UNORM format rejection.
- Whether ordinary Vulkan image-format query succeeds.
- Whether ColorBuffer creation proceeds beyond the Test4 abort.
- Whether GPU server stays alive.
- Whether Wayland produces sustained frames rather than stopping after one.
- Whether guest boot progresses and graphics are visible.

If fallback is not reached, inspect capability-query control flow and actual VkResult.
If reached but allocation fails, capture memory type bits, memory properties, allocation flags, and VkResult.
If allocation succeeds but later interop fails, identify which resource crosses the guest/host boundary and whether it genuinely requires AHB export.

Any next patch must address the next observed failure, not disable checks globally.

## Phase 2 — Map the Mali driver's actual capabilities
Add diagnostics, not speculative behavior:
- Vulkan physical-device name, vendor/device IDs, driver version.
- Relevant Vulkan extensions and feature bits.
- External-memory properties for Android hardware buffers.
- Image-format properties and usage/tiling combinations for formats gfxstream requests.
- AHardwareBuffer/gralloc format and usage support.
- Memory heaps/types and export/import compatibility.
- Mali kernel driver/JM UAPI version where available.

Keep diagnostics bounded and avoid device-unique identifiers.

## Phase 3 — Make gfxstream Mali-compatible incrementally
For each failing format or operation:
1. Confirm the exact Vulkan query and result.
2. Determine whether non-external/private allocation is semantically safe.
3. Check whether the resource is later shared with the guest or compositor.
4. Add a narrow per-format/per-usage fallback only when resource lifetime and sharing contract permit it.
5. Add a regression test or runtime diagnostic.
6. Build signed APK and verify package, ABI, libraries, certificate fingerprint, and hash.
7. Run same-machine device test and append outcome.

Do not silently report a format as supported if required usage or interop is missing. Avoid global feature spoofing.

## Phase 4 — Evaluate PanVK as a separate backend experiment
Before integration:
1. Inspect PanVK upstream and the kbase port's current source, license, commit history, open issues, and build instructions.
2. Confirm exact Mali-G57 product ID/revision and Job Manager (JM) backend support.
3. Establish whether T606 kernel mali_kbase UAPI is supported.
4. Determine whether app UID can access required kernel interfaces on stock Android 13; do not assume root.
5. Validate basic Vulkan device enumeration and a small offscreen render on the exact phone.
6. Validate Android WSI and gralloc/AHardwareBuffer interop separately.
7. Only then prototype a NestBox-selectable custom ICD/loader route, isolated behind a build/runtime option.

Do not substitute a CSF-only profile for JM. Do not bundle an experimental driver as the default renderer.

## Phase 5 — Performance and compatibility
After stable acceleration:
- Measure guest frame pacing and render throughput.
- Compare accelerated and software fallback using the same guest workload/resolution.
- Check memory pressure, thermal behavior, and sustained stability.
- Verify common GLES/Vulkan guest applications and compositor paths.
- Retain safe software-rendering fallback.

## Definition of done
- GPU server remains alive through guest boot and sustained rendering.
- Guest display updates continuously; no one-frame-only compositor exit.
- Host logs show real Mali Vulkan device use, not CPU-only fallback.
- No repeated fatal ColorBuffer / external-memory errors.
- Basic 2D and 3D workloads render correctly.
- Performance is measurably better than software rendering.
- No regression to Vulkan dispatch or mDNS fixes.
- APK is signed with permanent NestBox certificate and independently verified.


## 2026-11-18 update — Baseline startup is promising
- User reports Build #61 starts normally, reaches Android home, and has no GPU-server exit during startup. This is an initial positive result, not a diagnostics-confirmed GPU pass.
- User reports slight, barely noticeable lag; possible contributors mentioned are low-performance mode and host background apps. No cause has been isolated.
- Keep Build #61 in place. Next priority is optional diagnostics verification and sustained rendering confirmation, not another reinstall or immediate patch.
- Record virtual RAM as a user-observed possible host-memory-pressure improvement, but do not treat it as proven or as a guest RAM/GPU upgrade.
