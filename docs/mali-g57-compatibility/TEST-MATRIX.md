# Test matrix and acceptance criteria

## Test matrix

| Test ID | Build / path | Device state | What to verify | Status |
|---|---|---|---|---|
| T4 | Build #56 | Existing itel P55 machine | R8_UNORM AHB ColorBuffer crash | Failed; evidence recorded |
| T5 | Build #61 | Same machine; app update only | Non-AHB R8/R16 fallback, GPU server survival, sustained frames, guest boot | Awaiting user report |
| T6+ | Next targeted build | Same machine | One newly observed failure at a time | Not started |
| SW-1 | GPU acceleration disabled | Same machine | Software fallback boots; renderer/performance baseline if available | User reports boot, slower |
| PVK-1 | PanVK standalone prototype | Exact T606/G57 device | JM backend, Vulkan enumeration, offscreen rendering | Not started |
| PVK-2 | PanVK Android integration prototype | Exact device | Loader, WSI, gralloc/AHB, presentation | Not started |

## Test5 checklist
- [ ] Build #61 installed as an update; no ROM reinstall or machine deletion.
- [ ] Same existing machine used.
- [ ] GPU acceleration enabled.
- [ ] Guest reaches boot / launcher.
- [ ] GPU server remains alive.
- [ ] Wayland/compositor continues producing frames.
- [ ] R8/R16 non-external fallback log appears when expected.
- [ ] No R8_UNORM ColorBuffer abort.
- [ ] No new fatal host crash.
- [ ] Diagnostics archive saved intact.

## Result classification
**Pass:** accelerated renderer remains alive, guest display updates continuously, and guest boots.

**Partial:** targeted R8 failure is passed but a later graphics initialization or rendering operation fails. Record the next exact failure and continue.

**Fail / unchanged:** same R8/AHB fatal abort, fallback not reached, or GPU server exits at the same stage. Inspect why before changing another subsystem.

## Build verification checklist
For every APK:
- [ ] Workflow run and commit SHA recorded.
- [ ] Artifact downloaded and ZIP integrity checked.
- [ ] APK package is app.nbox.
- [ ] ARM64 native libraries present.
- [ ] APK signature verifies.
- [ ] Signing certificate SHA-256 matches permanent release fingerprint:
  1dd1cfb8846ef3ddb439c1c8b232f2c40f9075f583632cc8d8235c20c09c6bc4
- [ ] APK SHA-256 recorded.
- [ ] Build number and patch summary recorded.
