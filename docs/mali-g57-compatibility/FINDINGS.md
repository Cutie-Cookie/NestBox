# Findings and evidence

Observed facts are separated from hypotheses. A hypothesis is not confirmed until a test establishes it.

## F-001 — Host GPU is detected
**Status:** Confirmed from Test4.

Host log:
~~~
GFXSTREAM: Selecting Vulkan device: Mali-G57, Version: 1.3.225
GFXSTREAM: Using Vulkan externalMemoryMode: AndroidAHB
~~~

Interpretation: gfxstream reaches the Android Vulkan driver and selects Mali-G57. This is not simply a failure to find Vulkan or an Adreno-only device-selection check.

## F-002 — Test4 aborts creating an R8_UNORM ColorBuffer
**Status:** Confirmed from Test4.

Host log:
~~~
Failed to find memory type for creating buffer.
Format VK_FORMAT_R8_UNORM [9] is not supported.
Failed to create ColorBufferVk:10
Failed to initialize ColorBufferVk.
Failed to create ColorBuffer:10 format:26 with:4 height:4
Fatal signal 6 (SIGABRT)
~~~

Stack proceeds through gfxstream ColorBuffer creation and Virtio-GPU resource creation.

Interpretation: the immediate fatal path is a 4x4 R8_UNORM ColorBuffer creation using the AndroidAHB external-memory route. This does not prove every Vulkan feature or every Mali format is unsupported.

## F-003 — Build #61 contains a per-format non-AHB fallback
**Status:** Implemented in Build #61; device result pending.

If an R8_UNORM or R16_UNORM image query with Android hardware-buffer external memory returns VK_ERROR_FORMAT_NOT_SUPPORTED, gfxstream retries the ordinary Vulkan image-format query. If ordinary image creation is supported, that format is marked supported but not externally shareable. Image creation and allocation then avoid the AHB external-memory chain/export for that format and use ordinary Vulkan device memory.

Build details:
- Workflow: https://github.com/Cutie-Cookie/NestBox/actions/runs/44104470104
- Commit: 453f5cfb7d8c16e611742051200d93d3b5b9855e
- APK SHA-256: 68a137d9ea08ab71bbd788c99993007a4d763573efbda126a530cf377d0707ab

No device-side Test5 result has been received yet. Do not mark this fix successful until logs confirm the fallback and the GPU server survives.

## F-004 — Vulkan global entrypoint initialization was previously fixed
**Status:** Earlier test evidence confirmed the missing global Vulkan entrypoint errors disappeared after dispatch initialization was corrected. Preserve this fix.

## F-005 — mDNS high-FD crash was previously fixed
**Status:** Earlier tests confirmed the FD_SET overflow / tombstone no longer occurred after lowering the reserved FD floor from 1000 to 512. Preserve this fix.

## F-006 — Software-rendering path boots
**Status:** User observation.

With GPU acceleration disabled, the guest boots but is noticeably slower. This is consistent with software-rendering fallback, but exact renderer selection and performance have not been measured.

## F-007 — PanVK / panfrost-kbase is a possible alternative, not a drop-in fix
**Status:** Research lead; unverified on this phone.

PanVK is Mesa's Vulkan driver for Mali. A related experimental kbase port describes an Android Bionic ICD loading PanVK and issuing Mali kbase ioctls. Examined documentation describes:
- An Android driver path through a Bionic ICD, Android WSI, AHardwareBuffer/gralloc interop, PanVK core, and kbase backend.
- Separate CSF and JM backend concerns.
- A G615 MC6 / CSF reference device for some newer experiments.
- G57 JM-specific work and caveats in related development history.

Repository leads:
- https://github.com/zenithblue-oss/panvk-kbase-android
- https://github.com/JimVulkan/mali-panvk
- Mesa upstream: https://gitlab.freedesktop.org/mesa/mesa

Critical caveats:
1. A G615 CSF profile is not evidence of compatibility with T606 Mali-G57 MP1 / JM.
2. Android WSI and AHardwareBuffer/gralloc interoperability are separate from basic Vulkan device creation.
3. Bundling a custom ICD library does not activate it automatically; NestBox needs a deliberate loader/wrapper route.
4. Host renderer dependencies on Android loader/platform integration must be inspected.
5. Experimental claims and maturity must be independently verified.

## F-008 — PanVK should not be the first intervention
**Status:** Engineering decision.

Test Build #61 first because it directly targets the fatal operation observed in Test4 while preserving gfxstream. Replacing the renderer before validating this patch would add variables and obscure diagnosis.

## Open questions
- Does the R8/R16 non-AHB fallback execute on the device?
- Does ordinary R8_UNORM image allocation succeed on this Mali driver?
- Does gfxstream later require AHB sharing for a resource that fell back to private device memory?
- Are other unsupported formats or external-memory paths encountered afterward?
- Which Mali kernel interface / JM UAPI version is present?
- Is a compatible PanVK JM backend mature enough for this GPU?
- Can a custom Vulkan ICD be loaded safely inside NestBox without disturbing Android's system Vulkan stack?
