#!/usr/bin/env python3
"""Expand rootless failure diagnostics without changing guest boot behavior."""
import sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
if "Host AArch32:" in s:
    raise SystemExit("already patched: start from a clean Wayondroid rootless_instance.cpp")

old = '''    out += "Instance: " + layout_.work + "\\n";
    const std::pair<const char*, size_t> logs[] = {
        {"prepare.log", 5}, {"init.log", 30}, {"binderd.log", 10}, {"vine_wl.log", 10}, {"vine_pulse.log", 5}, {"vine_kumquat.log", 10}};
'''
new = '''    out += "Instance: " + layout_.work + "\\n";
    out += std::string("Host AArch32: ") + (cfg_.host_has_32bit ? "yes" : "no") + "\\n";
    out += "Host ABIs: ";
    const auto abis = host_abi_list();
    for (size_t i = 0; i < abis.size(); ++i) out += (i ? ", " : "") + abis[i];
    out += "\\n";
    const std::pair<const char*, size_t> logs[] = {
        {"prepare.log", 100}, {"init.log", 120}, {"binderd.log", 40}, {"vine_wl.log", 30}, {"vine_pulse.log", 20}, {"vine_kumquat.log", 30}};
'''
if old not in s:
    raise SystemExit("diagnostics log block not found; refusing partial patch")
s = s.replace(old, new, 1)
old_kmsg = 'const std::string kmsg = tail_file(layout_.rootfs + "/dev/kmsg", 40);'
new_kmsg = 'const std::string kmsg = tail_file(layout_.rootfs + "/dev/kmsg", 160, 262144);'
if old_kmsg not in s:
    raise SystemExit("kmsg tail line not found; refusing partial patch")
s = s.replace(old_kmsg, new_kmsg, 1)
open(path, "w", encoding="utf-8").write(s)
print("patched rootless diagnostics")
