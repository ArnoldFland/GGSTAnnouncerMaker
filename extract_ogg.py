from pathlib import Path
import struct

src = Path("extracted/Counter/NA_1501_Btl_Counter.uexp")
dst = Path("output/Chaos_Counter.ogg")

data = src.read_bytes()

start = data.find(b"OggS")
if start == -1:
    raise RuntimeError("找不到 OggS")

size = struct.unpack_from("<I", data, start - 16)[0]

ogg = data[start:start + size]
dst.write_bytes(ogg)

print("OggS:", hex(start))
print("OGG size:", size)
print("输出:", dst)