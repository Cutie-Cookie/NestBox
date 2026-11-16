#!/usr/bin/env python3
"""Merge every non-signature entry missing from the original 0.4.0 APK.

The newly built APK wins on colliding paths (manifest, resources and updated code).
All original-only entries, including Classic/Twoyi libraries, classes14.dex and
Commons Codec resources, are carried into the result. The final APK is re-signed
by the workflow after this ZIP operation.
"""
import hashlib
import re
import struct
import sys
import zipfile
from pathlib import Path

original = Path(sys.argv[1])
built = Path(sys.argv[2])
expected = "50049680418b072934360af4116c01b5a194af6a90459fd21cdb26b3b68cfa05"

digest = hashlib.sha256(original.read_bytes()).hexdigest()
if digest != expected:
    raise SystemExit(f"Original APK SHA-256 mismatch: {digest}")

signature_suffixes = (".RSA", ".DSA", ".EC", ".SF")
def is_signature_entry(name):
    upper = name.upper()
    return upper.startswith("META-INF/") and (
        upper.endswith(signature_suffixes) or upper.endswith("/MANIFEST.MF")
        or upper == "META-INF/MANIFEST.MF"
    )

def dex_classes(data):
    if not data.startswith(b"dex\\n"):
        raise SystemExit("Invalid DEX header while checking original classes")
    string_count, string_off = struct.unpack_from("<II", data, 56)
    type_count, type_off = struct.unpack_from("<II", data, 64)
    class_count, class_off = struct.unpack_from("<II", data, 96)

    def read_uleb(pos):
        value = shift = 0
        while True:
            byte = data[pos]
            pos += 1
            value |= (byte & 0x7f) << shift
            if byte < 0x80:
                return value, pos
            shift += 7

    def string_at(index):
        if index >= string_count:
            raise SystemExit("DEX string index out of range")
        off = struct.unpack_from("<I", data, string_off + index * 4)[0]
        _, pos = read_uleb(off)  # UTF-16 length; descriptor bytes are ASCII
        end = data.index(b"\\0", pos)
        return data[pos:end].decode("utf-8", "strict")

    classes = set()
    for i in range(class_count):
        class_idx = struct.unpack_from("<I", data, class_off + i * 32)[0]
        if class_idx >= type_count:
            raise SystemExit("DEX type index out of range")
        descriptor_idx = struct.unpack_from("<I", data, type_off + class_idx * 4)[0]
        classes.add(string_at(descriptor_idx))
    return classes

tmp = built.with_suffix(".merged.apk")
with zipfile.ZipFile(original, "r") as src, zipfile.ZipFile(built, "r") as current:
    current_names = set(current.namelist())
    original_names = set(src.namelist())
    current_dex = [n for n in current_names if re.fullmatch(r"classes(?:[2-9][0-9]*)?\\.dex", n)]
    current_classes = set()
    for name in current_dex:
        current_classes.update(dex_classes(current.read(name)))
    old_dex = [n for n in src.namelist() if re.fullmatch(r"classes(?:[2-9][0-9]*)?\\.dex", n) and n not in current_names]
    for name in old_dex:
        overlap = current_classes.intersection(dex_classes(src.read(name)))
        if overlap:
            sample = ", ".join(sorted(overlap)[:5])
            raise SystemExit(f"Refusing to merge {name}: {len(overlap)} duplicate classes already exist in the new build (e.g. {sample})")
    added = [n for n in src.namelist() if n not in current_names and not is_signature_entry(n)]
    skipped_signatures = [n for n in src.namelist() if is_signature_entry(n)]
    collisions = sorted(n for n in original_names & current_names if not is_signature_entry(n))
    with zipfile.ZipFile(tmp, "w") as out:
        for info in current.infolist():
            if is_signature_entry(info.filename):
                continue
            out.writestr(info, current.read(info.filename))
        for name in added:
            info = src.getinfo(name)
            out.writestr(info, src.read(name))
    with zipfile.ZipFile(tmp, "r") as merged:
        merged_names = set(merged.namelist())
        missing = sorted(n for n in original_names if not is_signature_entry(n) and n not in merged_names)
        if missing:
            raise SystemExit("Original APK entries still missing: " + ", ".join(missing[:30]))
        for required in ("classes14.dex", "lib/arm64-v8a/libOpenglRender.so",
                         "lib/arm64-v8a/libloader.so", "lib/arm64-v8a/libtwoyi.so"):
            if required not in merged_names:
                raise SystemExit("Required original component missing: " + required)

tmp.replace(built)
print(f"Original APK verified: {len(original_names)} entries")
print(f"Added original-only entries: {len(added)}")
print(f"Kept current-build versions for colliding paths: {len(collisions)}")
print(f"Removed obsolete original signature entries: {len(skipped_signatures)} (APK will be re-signed)")
print("Verified all original non-signature entry paths are present.")
