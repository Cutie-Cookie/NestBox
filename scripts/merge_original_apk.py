#!/usr/bin/env python3
"""Merge original APK-only files while avoiding duplicate runtime DEX classes."""
import hashlib
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

original = Path(sys.argv[1])
built = Path(sys.argv[2])
baksmali_jar = Path(sys.argv[3])
smali_jar = Path(sys.argv[4])
expected = "68a137d9ea08ab71bbd788c99993007a4d763573efbda126a530cf377d0707ab"

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
    if not data.startswith(b"dex\n"):
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
        _, pos = read_uleb(off)
        end = data.index(b"\0", pos)
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
    current_dex = [n for n in current_names if re.fullmatch(r"classes(?:[0-9]+)?\.dex", n)]
    current_classes = set()
    for name in current_dex:
        current_classes.update(dex_classes(current.read(name)))

    original_dex_name = "classes14.dex"
    original_backup_name = "assets/nestbox/original/classes14.dex"
    if original_dex_name not in src.namelist() or original_dex_name in current_names:
        raise SystemExit("Expected Build 61 classes14.dex was not found or already exists in current build")
    if original_backup_name not in src.namelist():
        raise SystemExit("Build 61 reference is missing the byte-for-byte original classes14.dex backup")

    # The old DEX shares many dependency definitions with the newer build.
    # Disassemble it, remove class definitions already supplied by current DEX
    # files, then reassemble the remaining original-only classes.
    with tempfile.TemporaryDirectory(prefix="nestbox-dex-merge-") as td:
        root = Path(td)
        old_dex = root / original_dex_name
        old_dex.write_bytes(src.read(original_dex_name))
        smali_dir = root / "smali"
        subprocess.run(
            ["java", "-jar", str(baksmali_jar), "disassemble", str(old_dex), "-o", str(smali_dir)],
            check=True,
        )
        removed_classes = 0
        kept_classes = 0
        for smali_file in smali_dir.rglob("*.smali"):
            descriptor = None
            for line in smali_file.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith(".class "):
                    descriptor = line.split()[-1]
                    break
            if descriptor is None:
                raise SystemExit(f"Could not read class descriptor from {smali_file}")
            if descriptor in current_classes:
                smali_file.unlink()
                removed_classes += 1
            else:
                kept_classes += 1
        filtered_dex = root / "classes14.filtered.dex"
        subprocess.run(
            ["java", "-jar", str(smali_jar), "assemble", str(smali_dir), "-o", str(filtered_dex)],
            check=True,
        )
        filtered_dex_bytes = filtered_dex.read_bytes()
        filtered_classes = dex_classes(filtered_dex_bytes)
        overlap = current_classes.intersection(filtered_classes)
        if overlap:
            raise SystemExit(f"Filtered classes14.dex still has {len(overlap)} duplicate classes")
        # Build 61 already contains the filtered runtime DEX plus the exact original DEX backup.
        # Preserve the backup, not the already-filtered runtime copy.
        original_dex_bytes = src.read(original_backup_name)
        print(f"Original classes14.dex: retained {kept_classes} unique classes; removed {removed_classes} duplicate definitions")

    added = [n for n in src.namelist() if n not in current_names and n not in (original_dex_name, original_backup_name) and not is_signature_entry(n)]
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
        out.writestr("classes14.dex", filtered_dex_bytes, compress_type=zipfile.ZIP_DEFLATED)
        out.writestr("assets/nestbox/original/classes14.dex", original_dex_bytes, compress_type=zipfile.ZIP_DEFLATED)

with zipfile.ZipFile(tmp, "r") as merged:
    merged_names = set(merged.namelist())
    missing = sorted(n for n in original_names if not is_signature_entry(n) and n != original_dex_name and n not in merged_names)
    if missing:
        raise SystemExit("Original APK entries still missing: " + ", ".join(missing[:30]))
    if original_dex_name not in merged_names or "assets/nestbox/original/classes14.dex" not in merged_names:
        raise SystemExit("Filtered runtime DEX or preserved original DEX asset is missing")
    all_dex = [n for n in merged_names if re.fullmatch(r"classes(?:[0-9]+)?\.dex", n)]
    all_classes = set()
    for name in all_dex:
        parsed = dex_classes(merged.read(name))
        overlap = all_classes.intersection(parsed)
        if overlap:
            raise SystemExit(f"Duplicate DEX classes remain after merge in {name}: {len(overlap)}")
        all_classes.update(parsed)
    for required in (
        "classes14.dex",
        "assets/nestbox/original/classes14.dex",
        "lib/arm64-v8a/libOpenglRender.so",
        "lib/arm64-v8a/libloader.so",
        "lib/arm64-v8a/libtwoyi.so",
    ):
        if required not in merged_names:
            raise SystemExit("Required original component missing: " + required)

tmp.replace(built)
print(f"Original APK verified: {len(original_names)} entries")
print(f"Added original-only entries: {len(added)}")
print(f"Kept current-build versions for colliding paths: {len(collisions)}")
print(f"Removed obsolete original signature entries: {len(skipped_signatures)} (APK will be re-signed)")
print("Verified all original non-signature entry paths; original classes14.dex is preserved byte-for-byte as an asset, with unique classes retained in runtime classes14.dex.")
