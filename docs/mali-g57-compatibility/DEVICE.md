# Target device profile

## User-reported / project-recorded details

| Item | Value | Confidence / source |
|---|---|---|
| Phone | itel P55 | User |
| Device model | A666L | Existing NestBox diagnostic |
| Android | Android 13 | Existing NestBox diagnostic |
| SoC | Unisoc T606 | User/project context |
| GPU | Arm Mali-G57 | User/project context and host Vulkan log |
| GPU configuration | MP1 reported | Public device-spec listings; verify on device |
| Vulkan API | 1.3.225 | Test4 host log |
| GPU selected by gfxstream | Mali-G57 | Test4 host log |
| External memory mode | AndroidAHB | Test4 host log |
| GPU acceleration toggle | Enabled path crashes; disabled path boots more slowly | User observation |

## Important distinctions
- Mali-G57 is an Arm Valhall-family GPU, not an Adreno GPU.
- Mali-G57 variants and kernel interfaces differ. Do not assume a driver tested on G57 MC2 / CSF works on this T606 G57 MP1 device.
- T606 is expected to use the Mali Job Manager (JM) family, not the newer Command Stream Frontend (CSF) path described in some PanVK experiments. Verify exact kernel UAPI before selecting a backend.
- Vulkan API version alone does not prove support for a format, external-memory handle, AHardwareBuffer import/export, or modifier.

## Device facts still to collect
Where possible, obtain these through diagnostics without asking the user to change settings:
1. ro.hardware, ro.board.platform, SoC/GPU renderer strings.
2. Vulkan physical-device properties and driver properties.
3. Supported instance/device extensions.
4. VkPhysicalDeviceExternalMemory capability results for Android hardware buffers.
5. Format properties for formats gfxstream uses, including R8/R16 and common color/depth formats.
6. Android gralloc/AHardwareBuffer format and usage support.
7. Mali kernel driver version and JM UAPI version, if readable without root.
8. App-UID access to required device nodes and sync primitives; never assume root access.

Do not request IMEI, serial number, or account details.


## 2026-11-18 — Host virtual RAM and responsiveness note
- User reports virtual RAM enabled on the phone appears to improve ROM/NestBox responsiveness.
- Configured virtual RAM amount and implementation details have not been recorded.
- Possible mechanism: host memory pressure relief / fewer background process evictions. Virtual RAM is storage-backed and much slower than physical memory; it does not directly add RAM to the NestBox guest or GPU capacity.
- Subjective performance note only; no benchmark or controlled comparison yet.
