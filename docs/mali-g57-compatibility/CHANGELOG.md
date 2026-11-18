

## 2026-11-18 — User-reported Build #61 startup success (initial Test5 observation)

### Device result
- User installed Build #61 as an app update and tested the existing ROM/machine; no ROM reinstall or machine recreation was reported.
- NestBox opened normally and the guest reached Android's home screen.
- User reports no GPU-server exit/crash during this successful startup.
- User reports the guest is still a little laggy, but the lag is barely noticeable.
- User attributes possible lag partly to the current low-performance configuration and multiple apps running in the phone's background; these are plausible factors, not measured causes.

### Interpretation / limits
- This is a meaningful positive result and supports that Build #61's targeted R8/R16 fallback may have avoided the Test4 startup abort.
- The result is currently user-reported behavior only. No Test5 diagnostics archive or log confirmation has been received yet.
- Normal boot and GPU-server survival do not alone prove that all guest graphics are hardware-rendered or that acceleration/performance is fully correct.
- Do not claim a completed GPU compatibility pass, sustained frame rendering, or benchmark improvement until diagnostics and/or a sustained graphics test confirm them.
- Keep Build #61 as the working baseline. Do not ask the user to reinstall the ROM, recreate the machine, wipe data, or change phone settings for this observation.

### Virtual RAM / host memory observation
- User noticed that enabling virtual RAM on the phone appears to make ROMs/NestBox feel faster or smoother.
- Amount of virtual RAM enabled is unknown; this is a subjective observation, not a benchmark.
- Possible explanation: storage-backed swap can reduce host memory pressure and help background apps/processes remain resident, but it is far slower than physical RAM and does not increase NestBox guest-assigned RAM or GPU capability. Improvement may depend on workload and device swap implementation.
- Treat this as a performance observation to revisit during later controlled comparisons, not as established causation.

### Updated next steps
1. Keep Build #61 installed and use it normally; collect diagnostics only if/when convenient or if a problem occurs.
2. If diagnostics become available, verify fallback log, GPU-server process, Wayland/compositor frame count, and whether actual Mali rendering is used.
3. Avoid changing multiple variables (performance profile, background apps, virtual RAM, resolution) at once; if comparing performance, record conditions first.
4. Continue targeted Mali-G57 compatibility work after the current baseline is documented and verified; PanVK remains a separate research path, not a promised performance upgrade.
