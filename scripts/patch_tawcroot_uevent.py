#!/usr/bin/env python3
"""Teach the rootless uevent stub to accept SO_RCVBUFFORCE.

Android 13's uevent_open_socket() sets SO_RCVBUF, reads it back, and if the
effective buffer is below twice the requested size, tries SO_RCVBUFFORCE.
The guest's uevent socket is represented by an AF_UNIX datagram stub, which
cannot provide a kernel netlink receive queue. The force option is therefore
irrelevant for this silent stub; failing it makes uevent_open_socket() close
the descriptor and init abort with "Could not open uevent socket".
"""
import sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()

if "TAWC_UEVENT_RCVBUFFORCE_COMPAT" in s:
    raise SystemExit("already patched: start from clean Wayondroid syscalls_socket.c")

needle = "#define SO_PEERCRED_OPT 17\n"
if needle not in s:
    raise SystemExit("SO_PEERCRED definition not found; refusing partial patch")
s = s.replace(
    needle,
    needle + "#define SO_RCVBUFFORCE_OPT 33 /* Linux SO_RCVBUFFORCE */\n",
    1,
)

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
new = "tawcroot_dispatch_install(TAWC_SYS_setsockopt, handle_setsockopt);"
if old not in s:
    raise SystemExit("lazy setsockopt registration not found; refusing partial patch")
s = s.replace(old, new, 1)

open(path, "w", encoding="utf-8").write(s)
print("patched uevent-stub SO_RCVBUFFORCE compatibility")
