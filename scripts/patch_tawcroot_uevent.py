#!/usr/bin/env python3
"""Make Android 13's rootless uevent AF_UNIX stub accept its buffer setup.

Android 13 uevent_open_socket() sets SO_RCVBUF, reads it back, and may then
request SO_RCVBUFFORCE. A silent AF_UNIX uevent stub has no kernel event queue,
so the forced buffer size is immaterial. The option must be intercepted only
for the tagged uevent stub; ordinary sockets keep native behavior.
"""
import sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()

if "TAWC_UEVENT_RCVBUFFORCE_COMPAT" in s:
    raise SystemExit("already patched: start from clean Wayondroid syscalls_socket.c")

needle = '#include "fdtab.h"\n'
if needle not in s:
    raise SystemExit("fdtab include not found; refusing partial patch")
s = s.replace(needle, needle + '#include "filter.h"\n', 1)

needle = "#define SO_PEERCRED_OPT 17\n"
if needle not in s:
    raise SystemExit("SO_PEERCRED definition not found; refusing partial patch")
s = s.replace(
    needle,
    needle + "#define SO_RCVBUFFORCE_OPT 33 /* Linux SO_RCVBUFFORCE */\n",
    1,
)

needle = "/* Create a stub for a denied uevent socket."
if needle not in s:
    raise SystemExit("uevent stub implementation not found; refusing partial patch")

filter_helper = r'''/* The uevent stub's setsockopt handler is lazy, like netemu's. Install
 * its trap before returning the new fd, so ueventd's immediate socket
 * configuration reaches handle_setsockopt(). */
static long ensure_uevent_setsockopt_filter(void)
{
    static int lock;
    static int ready;
    while (__atomic_exchange_n(&lock, 1, __ATOMIC_ACQUIRE)) {}
    long result = 0;
    if (tawcroot_namespace.session & TAWC_NS_FAKE_NET) ready = 1;
    if (!ready) {
        const int lazy[] = { TAWC_SYS_setsockopt };
        result = tawcroot_install_lazy_filter(lazy, 1);
        if (result == 0) ready = 1;
    }
    __atomic_store_n(&lock, 0, __ATOMIC_RELEASE);
    return result;
}

'''
s = s.replace(needle, filter_helper + needle, 1)

old = '''\t\tif (e == 0) return fd;
\t\tif (e != TAWC_EADDRINUSE) break;'''
new = '''\t\tif (e == 0) {
            long filter_result = ensure_uevent_setsockopt_filter();
            if (filter_result < 0) {
                tawc_close((int)fd);
                return filter_result;
            }
            return fd;
        }
\t\tif (e != TAWC_EADDRINUSE) break;'''
if old not in s:
    raise SystemExit("uevent stub bind success block not found; refusing partial patch")
s = s.replace(old, new, 1)

needle = "void tawcroot_socket_register(void)\n{\n"
if needle not in s:
    raise SystemExit("socket registration function not found; refusing partial patch")

handler = r'''/* TAWC_UEVENT_RCVBUFFORCE_COMPAT:
 * Android 13's uevent_open_socket() may request SO_RCVBUFFORCE after
 * SO_RCVBUF readback. A uevent stub is an AF_UNIX datagram socket with no
 * kernel event queue, so its receive-buffer ceiling is immaterial. Returning
 * success here lets ueventd finish opening its deliberately silent monitor.
 * Do not relax this option for ordinary sockets or netlink emulation sockets.
 */
static long handle_setsockopt(const tawcroot_syscall_args *args, ucontext_t *uc)
{
    if (fd_is_uevent_stub((int)args->a) &&
        (int)args->b == SOL_SOCKET_LEVEL &&
        (int)args->c == SO_RCVBUFFORCE_OPT)
        return 0;
    return tawcroot_netemu_setsockopt(args, uc);
}

'''
s = s.replace(needle, handler + needle, 1)

old = "tawcroot_dispatch_install_lazy(TAWC_SYS_setsockopt, tawcroot_netemu_setsockopt);"
new = "tawcroot_dispatch_install_lazy(TAWC_SYS_setsockopt, handle_setsockopt);"
if old not in s:
    raise SystemExit("lazy setsockopt registration not found; refusing partial patch")
s = s.replace(old, new, 1)

open(path, "w", encoding="utf-8").write(s)
print("patched uevent-stub SO_RCVBUFFORCE compatibility and lazy syscall trap")
