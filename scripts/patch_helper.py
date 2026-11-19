"""NestBox patch for Wayondroid's rootless helper (a45f80b), app/src/main/cpp/rootless.

Adds the machine overlay NestBox applies before every boot (the first one included):

1. <instance>/nestbox.prop: system properties for the guest, written as a marked block at the end
   of /system/product/etc/build.prop on every start (product loads last, so it wins).
2. <instance>/nestbox.remove: guest paths to delete before boot (one per line), e.g. bloat apps,
   /system/xbin/su when root is off.
3. <instance>/nestbox.files/: a tree copied over the guest's root with its file modes (NestBox's su
   with the set-uid bit, nb-runas, files a ROM ships in assets/guest/<rom id>/).
4. <instance>/nestbox.shared: a phone folder (one path) bound at the guest's /nestbox_host and
   mounted at /data/media/0/Host, which apps see as /sdcard/Host. The mount runs on post-fs-data
   from /product/etc/init/nestbox-shared.rc, which init parses before vine-rootless.rc, so the
   recursive /data/media binds that make /storage carry it along.

Usage: python3 scripts/patch_helper.py <wayondroid-source>/app/src/main/cpp/rootless
       (patches rootless_prep.cpp and rootless_instance.cpp in that folder)
"""
import os
import sys

folder = sys.argv[1]
path = os.path.join(folder, "rootless_prep.cpp")
s = open(path, encoding="utf-8").read()
if "nb_apply_overlay" in s:
    raise SystemExit("already patched: start from a clean copy of rootless_prep.cpp")

# Android 11 Product properties live under system/product/etc/build.prop on the
# extracted system-as-root image. Sanitize that file too, or init still sees
# ro.product.cpu.abilist32 and starts the 32-bit BoringSSL self-test.
old_paths = 'for (const char* f : {"/system/build.prop", "/vendor/build.prop", "/vendor/odm/etc/build.prop"}) {'
new_paths = 'for (const char* f : {"/system/build.prop", "/system/product/etc/build.prop", "/vendor/build.prop", "/vendor/odm/etc/build.prop"}) {'
if new_paths not in s:
    if old_paths not in s:
        raise SystemExit("64-bit-only property rewrite loop not found; refusing to patch")
    s = s.replace(old_paths, new_paths, 1)

# The parser's partition-prefix logic does not match the base ro.product.cpu
# property names. Explicitly clear the base abilist32 and constrain abilist.
old_abi = 'if (rest == ".product.cpu.abilist") line = key + "=arm64-v8a";'
new_abi = 'if (key == "ro.product.cpu.abilist") line = key + "=arm64-v8a";\n        else if (key == "ro.product.cpu.abilist32") continue; // Remove trigger property entirely; empty values may still match init wildcard triggers.\n        else if (rest == ".product.cpu.abilist") line = key + "=arm64-v8a";'
if new_abi not in s:
    if old_abi not in s:
        raise SystemExit("ABI property rewrite cases not found; refusing to patch")
    s = s.replace(old_abi, new_abi, 1)

s = s.replace("#include <dirent.h>\n", "#include <dirent.h>\n#include <fcntl.h>\n#include <vector>\n", 1)

helpers = r'''
// ---- Android 11 rootless boot repair (recorded in docs/android11-rootless-boot-repair.md) ----
// Preserve exact imported init configuration before changing rootless-only behavior.
bool nb_backup_once(const std::string& src, const std::string& backup, std::string* error) {
    if (is_regular_file(backup)) return true;
    if (!mkdirs_or_fail(backup.substr(0, backup.rfind('/')), error)) return false;
    return copy_file_sparse(src, backup) || fail(error, "backup original init config: " + src);
}

// Remove only the reboot_on_failure service option from bpfloader's stanza.
std::string nb_make_bpfloader_nonfatal(const std::string& rc, bool* changed) {
    std::string out;
    bool in_service = false;
    for (const auto& line : split_lines(rc)) {
        const size_t first = line.find_first_not_of(" \t");
        const std::string trimmed = first == std::string::npos ? "" : line.substr(first);
        if (trimmed.rfind("service ", 0) == 0 || trimmed.rfind("on ", 0) == 0 ||
            trimmed.rfind("import ", 0) == 0) {
            in_service = trimmed.rfind("service bpfloader ", 0) == 0;
        } else if (trimmed.empty()) {
            in_service = false;
        }
        if (in_service && trimmed.rfind("reboot_on_failure ", 0) == 0) {
            *changed = true;
            continue;
        }
        out += line + "\n";
    }
    return out;
}

// ---- NestBox additions (see scripts/patch_helper.py) ----
namespace {

// nestbox.files: copies a tree over the rootfs, keeping each file's mode (set-uid included)
bool nb_copy_tree(const std::string& src, const std::string& dst, std::string* error) {
    DIR* d = opendir(src.c_str());
    if (!d) return true;
    bool ok = true;
    while (dirent* e = readdir(d)) {
        const std::string n = e->d_name;
        if (n == "." || n == "..") continue;
        const std::string from = src + "/" + n, to = dst + "/" + n;
        struct stat st{};
        if (lstat(from.c_str(), &st) != 0) continue;
        if (S_ISDIR(st.st_mode)) {
            ok = mkdirs_or_fail(to, error) && nb_copy_tree(from, to, error);
        } else if (S_ISREG(st.st_mode)) {
            struct stat old{};
            if (lstat(to.c_str(), &old) == 0 && !S_ISREG(old.st_mode)) ok = remove_if_exists(to, error);
            ok = ok && copy_mode(from, to, st.st_mode & 07777, error);
        }
        if (!ok) break;
    }
    closedir(d);
    return ok;
}

// Stage only guest-side ARM64 EGL/GLES drivers into Android's preferred vendor namespace.
// GSI and emulator trees sometimes keep their EGL implementation under /system/lib64/egl,
// while libEGL's native-driver loader searches /vendor/lib64/egl. Never follow a guest
// symlink here: rootfs absolute symlinks resolve against the phone when accessed by the host.
bool nb_arm64_elf(const std::string& path) {
    const auto h = read_file_prefix(path, 20);
    if (!h || h->size() < 20) return false;
    const auto* p = reinterpret_cast<const unsigned char*>(h->data());
    return p[0] == 0x7f && p[1] == 'E' && p[2] == 'L' && p[3] == 'F' &&
           p[4] == 2 && p[18] == 183 && p[19] == 0; // ELF64, EM_AARCH64
}

bool nb_egl_driver_name(const std::string& n) {
    if (n.size() < 4 || n.compare(n.size() - 3, 3, ".so") != 0 || n == "libGLES_android.so") return false;
    return n == "libGLES.so" || n == "libEGL.so" || n == "libGLESv1_CM.so" ||
           n == "libGLESv2.so" || n.rfind("libGLES_", 0) == 0 ||
           n.rfind("libGLESv1_CM_", 0) == 0 || n.rfind("libGLESv2_", 0) == 0 ||
           n.rfind("libEGL_", 0) == 0;
}

bool nb_stage_egl_drivers(const std::string& R, std::string* error) {
    const std::string vendor = R + "/vendor";
    struct stat vst{};
    if (lstat(vendor.c_str(), &vst) != 0 || !S_ISDIR(vst.st_mode)) {
        fprintf(stderr, "NestBox EGL: vendor root is not a real directory; refusing host-side symlink traversal\n");
        return true;
    }
    const std::string dst = vendor + "/lib64/egl";
    const std::string sources[] = {R + "/system/lib64/egl", R + "/system/lib64"};
    int copied = 0;
    for (const auto& src : sources) {
        struct stat st{};
        if (lstat(src.c_str(), &st) != 0 || !S_ISDIR(st.st_mode)) continue;
        DIR* d = opendir(src.c_str());
        if (!d) continue;
        while (dirent* e = readdir(d)) {
            const std::string n = e->d_name;
            if (n == "." || n == ".." || !nb_egl_driver_name(n)) continue;
            const std::string from = src + "/" + n;
            const std::string to = dst + "/" + n;
            struct stat fs{}, ts{};
            if (lstat(from.c_str(), &fs) != 0 || !S_ISREG(fs.st_mode) || !nb_arm64_elf(from)) continue;
            // A ROM/vendor driver already at the canonical path always wins.
            if (lstat(to.c_str(), &ts) == 0) continue;
            if (!mkdirs_or_fail(dst, error) || !copy_mode(from, to, 0644, error)) {
                closedir(d);
                return false;
            }
            ++copied;
            fprintf(stderr, "NestBox EGL: staged %s -> vendor/lib64/egl/%s\n", from.c_str(), n.c_str());
        }
        closedir(d);
    }
    fprintf(stderr, "NestBox EGL: staged %d ARM64 driver libraries; vendor/lib64/egl inventory:", copied);
    DIR* d = opendir(dst.c_str());
    if (d) {
        while (dirent* e = readdir(d)) {
            const std::string n = e->d_name;
            if (nb_egl_driver_name(n)) fprintf(stderr, " %s", n.c_str());
        }
        closedir(d);
    }
    fprintf(stderr, "\n");
    return true;
}

// Android 11 does not provide the ANGLE backend selected by recent Waydroid builds.
// If this imported guest is pre-Android 13, select the SwiftShader library already
// shipped in the guest vendor image instead of falling back to vendor/lib64/egl/libEGL.so.
bool nb_select_legacy_egl(const std::string& R, std::string* error) {
    int sdk = 0;
    const std::string build_props[] = {R + "/system/build.prop", R + "/system/system/build.prop"};
    for (const auto& path : build_props) {
        const auto text = read_file(path);
        if (!text) continue;
        const std::string key = "ro.build.version.sdk=";
        const size_t at = text->find(key);
        if (at == std::string::npos) continue;
        size_t end = at + key.size();
        while (end < text->size() && (*text)[end] >= '0' && (*text)[end] <= '9') {
            sdk = sdk * 10 + ((*text)[end] - '0');
            ++end;
        }
        if (sdk > 0) break;
    }
    if (sdk <= 0) {
        fprintf(stderr, "NestBox EGL: guest SDK could not be read; keeping Waydroid backend\n");
        return true;
    }
    if (sdk >= 33) {
        fprintf(stderr, "NestBox EGL: guest SDK %d; keeping ANGLE backend\n", sdk);
        return true;
    }
    const std::string swiftshader = R + "/vendor/lib64/egl/libEGL_swiftshader.so";
    struct stat swiftshader_stat{};
    if (lstat(swiftshader.c_str(), &swiftshader_stat) != 0 ||
        !S_ISREG(swiftshader_stat.st_mode) || !nb_arm64_elf(swiftshader)) {
        fprintf(stderr, "NestBox EGL: guest SDK %d but ARM64 SwiftShader is unavailable; keeping existing backend\n", sdk);
        return true;
    }
    const std::string prop = R + "/vendor/waydroid.prop";
    auto text = read_file(prop);
    if (!text) return fail(error, "could not read vendor/waydroid.prop for legacy EGL selection");
    const std::string key = "ro.hardware.egl=";
    const std::string value = key + "swiftshader";
    size_t at = 0;
    bool replaced = false;
    while ((at = text->find(key, at)) != std::string::npos) {
        const size_t end = text->find('\n', at);
        text->replace(at, end == std::string::npos ? text->size() - at : end - at, value);
        at += value.size();
        replaced = true;
    }
    if (!replaced) {
        if (!text->empty() && text->back() != '\n') text->push_back('\n');
        text->append(value + "\n");
    }
    if (!write_mode(prop, *text, 0644, error)) return false;
    fprintf(stderr, "NestBox EGL: guest SDK %d; selected ARM64 SwiftShader to avoid the incompatible ANGLE fallback\n", sdk);
    return true;
}

// nestbox.remove deleted, nestbox.prop into a marked block of /system/product/etc/build.prop,
// nestbox.files copied, the shared folder mount
bool nb_apply_overlay(const Layout& l, std::string* error) {
    const std::string R = l.rootfs;
    if (const auto list = read_file(l.instance + "/nestbox.remove")) {
        size_t at = 0;
        while (at < list->size()) {
            size_t nl = list->find('\n', at);
            std::string p = list->substr(at, nl == std::string::npos ? std::string::npos : nl - at);
            at = nl == std::string::npos ? list->size() : nl + 1;
            while (!p.empty() && (p.back() == '\r' || p.back() == ' ')) p.pop_back();
            if (p.size() < 2 || p[0] != '/' || p.find("..") != std::string::npos) continue;
            if (!remove_if_exists(R + p, error)) return false;
        }
    }
    const std::string props = read_file(l.instance + "/nestbox.prop").value_or("");
    // In the extracted system-as-root tree, /product is an absolute symlink
    // to /system/product. Following R/product on the host escapes R and can
    // address the phone's read-only /system/product. Always edit the real
    // extracted target under R/system/product.
    const std::string prop = R + "/system/product/etc/build.prop";
    if (!is_directory(R + "/system/product/etc"))
        return fail(error, "extracted product property directory is missing: " + R + "/system/product/etc");
    std::string text = read_file(prop).value_or("");
    const size_t b = text.find("\n# nestbox-begin");
    if (b != std::string::npos) {
        const size_t e = text.find("# nestbox-end", b);
        text.erase(b, e == std::string::npos ? std::string::npos : e + 14 - b);
    }
    while (!text.empty() && text.back() == '\n') text.pop_back();
    if (!props.empty()) text += "\n# nestbox-begin\n" + props + "\n# nestbox-end\n";
    else text += "\n";
    if (!write_mode(prop, text, 0644, error)) return false;
    if (props.find("ro.hardware.egl=swiftshader") != std::string::npos) {
        const auto verify = read_file(prop);
        if (!verify || verify->find("ro.hardware.egl=swiftshader") == std::string::npos)
            return fail(error, "rootless graphics property overlay verification failed at " + prop);
        fprintf(stderr, "NestBox: verified rootless graphics properties in %s\n", prop.c_str());
    }
    if (!nb_copy_tree(l.instance + "/nestbox.files", R, error)) return false;
    const std::string init_dir = R + "/system/product/etc/init";
    // left by NestBox 0.6-0.7 (Android 10 port)
    if (!remove_if_exists(init_dir + "/nestbox-storage-q.rc", error)) return false;
    const std::string shared_rc = init_dir + "/nestbox-shared.rc";
    if (!is_regular_file(l.instance + "/nestbox.shared")) return remove_if_exists(shared_rc, error);
    return mkdirs_or_fail(R + "/nestbox_host", error) && mkdirs_or_fail(init_dir, error) &&
           write_mode(shared_rc,
                      "# NestBox shared folder: the phone's folder (bound at /nestbox_host) as /sdcard/Host\n"
                      "on post-fs-data\n"
                      "    mkdir /data/media/0 0770 media_rw media_rw\n"
                      "    mkdir /data/media/0/Host 0770 media_rw media_rw\n"
                      "    mount none /nestbox_host /data/media/0/Host bind\n",
                      0644, error);
}

} // namespace
'''

anchor = "bool prepare_rootfs(const Layout& l, const PrepOptions& o, std::string* error) {\n"
if anchor not in s:
    raise SystemExit("prepare_rootfs not found")
s = s.replace(anchor, helpers + "\n" + anchor, 1)

tail = "    return mkdirs_or_fail(l.run + \"/pulse\", error);\n}"
if tail not in s:
    raise SystemExit("prepare_rootfs end not found")
s = s.replace(tail, "    if (!mkdirs_or_fail(l.run + \"/pulse\", error)) return false;\n    return nb_apply_overlay(l, error);\n}", 1)


# Fix the actual init-imported zygote file (not merely create a separate rc).
old_zygote = """        const std::string z = R + "/system/etc/init/hw";
        if (!is_regular_file(z + "/init.zygote64.rc")) {
            const auto z6432 = read_file(z + "/init.zygote64_32.rc");
            if (!z6432) return fail(error, "the image has neither init.zygote64.rc nor init.zygote64_32.rc");
            if (!write_mode(z + "/init.zygote64.rc", zygote64_rc(*z6432), 0644, error)) return false;
        }"""
new_zygote = """        const std::string z = R + "/system/etc/init/hw";
        // init imports init.zygote64_32.rc directly. A separate 64-only RC
        // does not neutralize the secondary zygote. Preserve original bytes.
        const std::string z6432_path = z + "/init.zygote64_32.rc";
        const auto z6432 = read_file(z6432_path);
        if (z6432) {
            const std::string backup = l.instance + "/nestbox-original/init.zygote64_32.rc";
            if (!nb_backup_once(z6432_path, backup, error)) return false;
            const std::string clean = zygote64_rc(*z6432);
            if (!write_mode(z6432_path, clean, 0644, error)) return false;
            if (!write_mode(z + "/init.zygote64.rc", clean, 0644, error)) return false;
        } else if (!is_regular_file(z + "/init.zygote64.rc")) {
            return fail(error, "the image has neither init.zygote64.rc nor init.zygote64_32.rc");
        }"""
if new_zygote not in s:
    if old_zygote not in s: raise SystemExit("zygote replacement anchor not found in upstream patch script")
    s=s.replace(old_zygote,new_zygote,1)

# Make bpfloader failures nonfatal only in rootless mode; keep service and trigger.
old_bpf = """    if (!copy_mode(o.lib_dir + "/libvine_lmkd.so", R + "/system/bin/vine_lmkd", 0755, error) ||
        !copy_mode(o.lib_dir + "/libvine_mediascan.so", R + "/system/bin/vine_mediascan", 0755, error))
        return false;"""
new_bpf = """    // Rootless hosts cannot reliably grant BPF kernel capabilities. The Android
    // 11 bpfloader.rc uses reboot_on_failure; that policy turns exit 2 into a
    // fatal boot reboot. Keep service/trigger, remove only that fatal option.
    const std::string bpf_rc = R + "/system/etc/init/bpfloader.rc";
    if (const auto rc = read_file(bpf_rc)) {
        bool changed = false;
        const std::string safe_rc = nb_make_bpfloader_nonfatal(*rc, &changed);
        if (changed) {
            const std::string backup = l.instance + "/nestbox-original/bpfloader.rc";
            if (!nb_backup_once(bpf_rc, backup, error) || !write_mode(bpf_rc, safe_rc, 0644, error)) return false;
        } else {
            fprintf(stderr, "NestBox boot repair: bpfloader.rc has no reboot_on_failure option to remove\\n");
        }
    } else {
        fprintf(stderr, "NestBox boot repair: bpfloader.rc missing; policy unchanged\\n");
    }
    if (!copy_mode(o.lib_dir + "/libvine_lmkd.so", R + "/system/bin/vine_lmkd", 0755, error) ||
        !copy_mode(o.lib_dir + "/libvine_mediascan.so", R + "/system/bin/vine_mediascan", 0755, error))
        return false;"""
if new_bpf not in s:
    if old_bpf not in s: raise SystemExit("bpfloader replacement anchor not found in upstream patch script")
    s=s.replace(old_bpf,new_bpf,1)


# Put system-side ARM64 EGL implementations in Android's preferred vendor EGL
# directory. Preserve any ROM/vendor implementation already installed there.
egl_anchor = 'if (!write_mode(R + "/vendor/waydroid.prop", waydroid_prop(o.dpi, o.gpu), 0644, error)) return false;'
egl_patch = egl_anchor + '\n    if (!nb_stage_egl_drivers(R, error)) return false;\n    if (!nb_select_legacy_egl(R, error)) return false;'
if egl_patch not in s:
    if egl_anchor not in s:
        raise SystemExit("vendor waydroid.prop write not found; refusing EGL staging patch")
    s = s.replace(egl_anchor, egl_patch, 1)

open(path, "w", encoding="utf-8").write(s)
print("patched", path)

# Patch Wayondroid AArch32 detection: ABI properties alone are not proof of kernel ELF32 support.
upath = os.path.join(folder, "../utils/vine_utils.cpp")
u = open(upath, encoding="utf-8").read()
start = u.find("bool host_supports_aarch32() {")
end = u.find("\nstd::vector<std::string> host_abi_list()", start)
if start < 0 or end < 0:
    raise SystemExit("host_supports_aarch32() layout changed; refusing unsafe patch")
old_fn = u[start:end]
if "NestBox kernel-first AArch32 detection" in old_fn:
    raise SystemExit("already patched: start from a clean Wayondroid source")
new_fn = '''bool host_supports_aarch32() {
    // NestBox kernel-first AArch32 detection. Android ABI props can advertise
    // ARM32 even when this execution environment cannot exec ARM32 ELF files.
    auto cpuinfo = read_file("/proc/cpuinfo");
    if (cpuinfo.has_value()) {
        const bool supported = cpuinfo->find("aarch32_el0") != std::string::npos;
        VINE_LOGI("AArch32: kernel cpuinfo aarch32_el0 -> %s", supported ? "supported" : "unsupported");
        return supported;
    }
    static const char* knobs[] = {
        "/proc/sys/abi/cp15_barrier_emulation",
        "/proc/sys/abi/setend_emulation",
        "/proc/sys/abi/swp_emulation",
    };
    for (const char* f : knobs) {
        if (path_exists(f)) { VINE_LOGI("AArch32: kernel compat knob %s -> supported", f); return true; }
    }
    char buf[PROP_VALUE_MAX] = {};
    __system_property_get("ro.product.cpu.abilist32", buf);
    if (buf[0] != '\\0') { VINE_LOGW("AArch32: kernel evidence unavailable; abilist32 fallback '%s'", buf); return true; }
    __system_property_get("ro.product.cpu.abilist", buf);
    if (strstr(buf, "armeabi") != nullptr) { VINE_LOGW("AArch32: kernel evidence unavailable; abilist fallback '%s'", buf); return true; }
    VINE_LOGI("AArch32: no kernel or ABI evidence -> unsupported");
    return false;
}'''
u = u[:start] + new_fn + u[end:]
open(upath, "w", encoding="utf-8").write(u)
print("patched", upath)
# rootless_instance.cpp: the shared folder joins the runtime's binds (init and exec alike)
ipath = os.path.join(folder, "rootless_instance.cpp")
t = open(ipath, encoding="utf-8").read()
if "nestbox.shared" in t:
    raise SystemExit("already patched: start from a clean copy of rootless_instance.cpp")
old = """             "/dev/pts:/dev/pts", l.run + ":/run/user/1000"}) {
        out.push_back("-b");
        out.push_back(b);
    }
    return out;
}"""
new = """             "/dev/pts:/dev/pts", l.run + ":/run/user/1000"}) {
        out.push_back("-b");
        out.push_back(b);
    }
    // NestBox: the phone folder shared with the guest (see patch_helper.py)
    if (const auto shared = read_file(l.instance + "/nestbox.shared")) {
        std::string host = *shared;
        while (!host.empty() && (host.back() == '\\n' || host.back() == '\\r' || host.back() == ' ')) host.pop_back();
        struct stat st{};
        if (!host.empty() && host[0] == '/' && host.find(':') == std::string::npos && stat(host.c_str(), &st) == 0 &&
            S_ISDIR(st.st_mode)) {
            out.push_back("-b");
            out.push_back(host + ":/nestbox_host");
        }
    }
    return out;
}"""
if old not in t:
    raise SystemExit("binds() not found in rootless_instance.cpp")
t = t.replace(old, new, 1)
open(ipath, "w", encoding="utf-8").write(t)
print("patched", ipath)
