"""Keep Wayondroid's datagram-socket receive trap below Android's FD_SETSIZE."""
import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
old = "#define TAWCROOT_RESERVED_FD_BASE 1000"
new = "#define TAWCROOT_RESERVED_FD_BASE 512"
if new in s:
    print("tawcroot reserved fd floor already 512")
elif old in s:
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("lowered tawcroot reserved fd floor: 1000 -> 512")
else:
    raise SystemExit("expected TAWCROOT_RESERVED_FD_BASE definition not found")
