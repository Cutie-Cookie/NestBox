# Android 11 rootless boot failure: AArch32 detection

## Status

Investigation branch: `fix/android11-aarch32-detection`

The Android 11 VROM currently fails during early init. The fatal sequence in the
2026-11-18 X11 diagnostic archive is:

```text
init: cannot execv('/system/bin/boringssl_self_test32') ... Exec format error
Service with 'reboot_on_failure' option failed
Reboot start, reason: reboot,boringssl-self-check-failed
```

The executable exists in the system image and is an ARM ELF32 PIE. APEX activation
and linkerconfig complete before this failure. The host advertises
`armeabi-v7a,armeabi`, but that advertisement alone does not prove that the
kernel execution path used by the rootless guest can execute ARM32 ELF files.

## Source-level finding

Wayondroid's `host_supports_aarch32()` currently checks
`ro.product.cpu.abilist32` and `ro.product.cpu.abilist` before checking
kernel evidence (`/proc/sys/abi/*` and `aarch32_el0` in `/proc/cpuinfo`).
NestBox's X11 logs show that this first property check succeeds, so the
runtime labels AArch32 supported without reaching the kernel checks.

Wayondroid's rootless preparation already has a 64-bit-only path when
`host_has_32bit` is false. It rewrites guest ABI properties and
`ro.zygote`, and derives `init.zygote64.rc` without the secondary
32-bit zygote. That path is intended to avoid starting 32-bit-only init
services on hosts that cannot execute them.

## Planned fix

1. Make kernel capability evidence authoritative when `/proc/cpuinfo` is
   readable; do not let a conflicting Android ABI property override it.
2. Retain ABI-property fallback only when kernel evidence is unavailable,
   with an explicit warning in logs.
3. Build the native helper from the pinned Wayondroid source and NestBox patch.
4. Validate the helper's reported capability and boot Android 11. A successful
   APK build alone is not proof of a successful guest boot.

## Validation checklist

- [ ] Host probe reports AArch32 based on kernel evidence, not only ABI props.
- [ ] ARM64-only hosts select the existing 64-bit guest preparation path.
- [ ] Android 11 reaches zygote without the BoringSSL 32-bit self-test reboot.
- [ ] Android 13 baseline still boots.
- [ ] APK builds and installs over the existing NestBox installation.

## Scope

No ROM image is modified by this investigation. APK import and guest networking
remain deferred until the Android 11 boot path is validated.
