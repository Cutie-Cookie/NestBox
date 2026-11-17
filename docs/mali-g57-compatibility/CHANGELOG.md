# Append-only change and experiment log

Record all changes, including documentation-only edits, build-script changes, failed patch attempts, reverted changes, commands, test reports, decisions, and builds. Newest entries go at the bottom. Never erase an unsuccessful experiment; mark it superseded.

## 2026-11-17 — Investigation opened

### Repository / branch
- Repository: Cutie-Cookie/NestBox
- Branch: mali-g57-compatibility
- Base commit: 453f5cfb7d8c16e611742051200d93d3b5b9855e (Build #61)
- Purpose: isolate Mali-G57 compatibility research and future targeted changes from the existing diagnostics branch.

### Initial evidence reviewed
- Test4 diagnostics identify host Vulkan device as Mali-G57, Vulkan 1.3.225.
- Gfxstream selected AndroidAHB external-memory mode.
- Fatal operation: 4x4 VK_FORMAT_R8_UNORM ColorBuffer creation; driver reported unsupported format / memory type and process aborted.
- Previous Vulkan global dispatch and mDNS FD_SET fixes remain in the base.
- Build #61 adds a narrow R8/R16 non-AHB fallback; device-side validation is pending.

### Research notes
- PanVK is a possible alternative Vulkan implementation for Mali.
- Experimental panvk-kbase work has distinct backend generations and Android integration requirements; a CSF-oriented G615 profile cannot be assumed to work on T606 Mali-G57 MP1.
- Exact JM UAPI, Android WSI, AHardwareBuffer/gralloc sharing, and driver loading remain unverified.
- Decision: test Build #61 before changing renderer architecture.

### Changes made in this entry
- Added docs/mali-g57-compatibility/ as the dedicated investigation folder.
- Added README, device profile, findings, plan, test matrix, and append-only changelog.
- No application source, build workflow, dependency, renderer, or APK changes made on this branch.
- No build triggered.

### Next action
Wait for user's Test5 report from Build #61. Append complete result and proceed according to PLAN.md.
