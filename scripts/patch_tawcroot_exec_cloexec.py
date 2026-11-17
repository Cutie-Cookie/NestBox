"""Restore Linux execve close-on-exec semantics before tawcroot jumps into a guest ELF.

The in-process ELF loader does not issue a real execve for the guest binary.
Without this pass, CLOEXEC service sockets inherited from Android init survive
into every guest service. mdnsd then receives a high socket fd and aborts in
FD_SET when it exceeds FD_SETSIZE (1024). tawcroot's own reserved fds must stay
open for path translation, so only non-reserved CLOEXEC descriptors are closed.
"""
import sys
from pathlib import Path

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

if "tawcroot_close_guest_cloexec_fds" in s:
    print("guest CLOEXEC cleanup already present")
    raise SystemExit(0)

include_marker = '#include "tawc_uapi.h"'
includes = '''#include "tawc_uapi.h"
#include <fcntl.h>
#include "dirent_filter.h"
#include "fdtab.h"'''
if include_marker not in s:
    raise SystemExit("loader_exec include marker not found")
s = s.replace(include_marker, includes, 1)

helper = r"""
/* A guest exec is an in-process ELF map/jump, not a kernel execve.
 * Reproduce the kernel's FD_CLOEXEC pass while preserving tawcroot's
 * own reserved descriptors (which are CLOEXEC too, but are required
 * by the rootfs path translator). This prevents init's service sockets
 * from leaking into every service it starts. */
static void tawcroot_close_guest_cloexec_fds(void)
{
	char buf[4096];
	for (int pass = 0; pass < 8; pass++) {
		long dirfd = tawc_openat(-100, "/proc/self/fd",
					 O_RDONLY | O_DIRECTORY | O_CLOEXEC, 0);
		if (dirfd < 0) return;
		long closed = 0;
		for (;;) {
			long n = tawc_getdents64((int)dirfd, buf, sizeof(buf));
			if (n <= 0) break;
			for (long off = 0; off + 19 <= n;) {
				unsigned short reclen;
				__builtin_memcpy(&reclen, buf + off + 16, 2);
				if (reclen < 20 || off + (long)reclen > n) break;
				const char *name = buf + off + 19;
				int has_nul = 0;
				for (long k = 19; k < (long)reclen; k++) {
					if (buf[off + k] == 0) { has_nul = 1; break; }
				}
				if (!has_nul) break;
				off += reclen;

				int fd;
				if (!tawcroot_dirent_filter_dname_to_fd(name, &fd) ||
				    fd == (int)dirfd || tawcroot_fd_is_reserved(fd))
					continue;
				long flags = tawc_fcntl(fd, F_GETFD, 0);
				if (flags >= 0 && (flags & FD_CLOEXEC) &&
				    tawc_close(fd) == 0)
					closed++;
			}
		}
		tawc_close((int)dirfd);
		if (closed == 0) break;
	}
}

"""

insert_marker = "void tawcroot_loader_exec(const struct tawc_loader_exec_args *args)"
if insert_marker not in s:
    raise SystemExit("loader_exec function marker not found")
s = s.replace(insert_marker, helper + insert_marker, 1)

call_marker = "\ttawcroot_proctitle_apply(args->guest_path, eff_argc, eff_argv);"
if call_marker not in s:
    raise SystemExit("loader exec final-jump marker not found")
s = s.replace(call_marker, call_marker + "\n\ttawcroot_close_guest_cloexec_fds();", 1)

path.write_text(s, encoding="utf-8")
print("patched guest CLOEXEC handling in", path)
