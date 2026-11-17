# Mali-G57 compatibility investigation

This directory is the working record for bringing NestBox's accelerated graphics path up on the itel P55 / Unisoc T606 / Arm Mali-G57 device.

**Documentation rule:** record every investigation, hypothesis, source, command, patch, build, test, result, and decision here. Small changes count. Append dated entries; do not erase unsuccessful experiments or silently rewrite history.

## Scope and guardrails
- Target: itel P55 (A666L), Android 13, Unisoc T606, Mali-G57 (reported MP1).
- Goal: hardware-accelerated graphics for the Android guest, not merely successful boot.
- Preserve existing NestBox functionality and permanent APK signing identity.
- No ROM reinstall, machine deletion, data wipe, or unnecessary device-setting changes.
- Keep software rendering as a fallback.
- Do not claim compatibility until device tests demonstrate it.
- Keep experimental driver work separate from the release path.

## Documents
- [Device profile](DEVICE.md)
- [Known evidence and hypotheses](FINDINGS.md)
- [Investigation and implementation plan](PLAN.md)
- [Change and experiment log](CHANGELOG.md)
- [Test matrix and acceptance criteria](TEST-MATRIX.md)

## Current status
**Documentation only.** Branch created from Build #61. No source-code changes on this branch yet. Build #61 is the current candidate to test for the R8_UNORM / Android Hardware Buffer fallback.

Last updated: 2026-11-17
