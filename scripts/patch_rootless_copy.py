#!/usr/bin/env python3
"""Replace Wayondroid rootless copy_mode's sparse-extent copy with a verified byte stream.

The guest rootfs is prepared on Android app storage. SEEK_DATA/SEEK_HOLE can misreport
allocated extents on some backing filesystems; treating ENXIO as a trailing hole can
silently install zero-filled graphics/HAL libraries. These files are small, so copy
them sequentially and verify the resulting length before installation.
"""
import sys
from pathlib import Path

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
if "nestbox_verified_plain_copy" in s:
    raise SystemExit("already patched")
old = """bool copy_mode(const std::string& src, const std::string& dst, mode_t mode, std::string* error) {
    const std::string tmp = dst + ".tmp";
    if (!copy_file_sparse(src, tmp)) return fail(error, "could not copy " + src);
    if (chmod(tmp.c_str(), mode) != 0 || rename(tmp.c_str(), dst.c_str()) != 0) {
        unlink(tmp.c_str());
        return fail_errno(error, "install " + dst);
    }
    return true;
}"""
new = r'''// nestbox_verified_plain_copy: never use SEEK_DATA/SEEK_HOLE for runtime binaries.
bool copy_mode(const std::string& src, const std::string& dst, mode_t mode, std::string* error) {
    const std::string tmp = dst + ".tmp";
    int in = open(src.c_str(), O_RDONLY | O_CLOEXEC);
    if (in < 0) return fail_errno(error, "open source " + src);
    struct stat source{};
    if (fstat(in, &source) != 0 || !S_ISREG(source.st_mode) || source.st_size <= 0) {
        close(in);
        return fail(error, "invalid source file " + src);
    }
    int out = open(tmp.c_str(), O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (out < 0) {
        close(in);
        return fail_errno(error, "open destination " + tmp);
    }
    char buffer[64 * 1024];
    bool ok = true;
    off_t total = 0;
    while (ok) {
        ssize_t n = read(in, buffer, sizeof(buffer));
        if (n < 0) {
            if (errno == EINTR) continue;
            ok = false;
            break;
        }
        if (n == 0) break;
        ssize_t done = 0;
        while (done < n) {
            ssize_t w = write(out, buffer + done, static_cast<size_t>(n - done));
            if (w < 0 && errno == EINTR) continue;
            if (w <= 0) { ok = false; break; }
            done += w;
        }
        total += done;
    }
    struct stat copied{};
    if (ok && (fstat(out, &copied) != 0 || total != source.st_size || copied.st_size != source.st_size))
        ok = false;
    if (close(in) != 0) ok = false;
    if (close(out) != 0) ok = false;
    if (!ok) {
        unlink(tmp.c_str());
        return fail(error, "incomplete byte-for-byte copy of " + src);
    }
    if (chmod(tmp.c_str(), mode) != 0 || rename(tmp.c_str(), dst.c_str()) != 0) {
        unlink(tmp.c_str());
        return fail_errno(error, "install " + dst);
    }
    return true;
}'''
if old not in s:
    raise SystemExit("expected copy_mode implementation not found; refusing to patch")
s = s.replace(old, new, 1)
s = s.replace("#include <cerrno>\n", "#include <cerrno>\n#include <fcntl.h>\n", 1)
path.write_text(s, encoding="utf-8")
print("patched verified sequential copy:", path)
