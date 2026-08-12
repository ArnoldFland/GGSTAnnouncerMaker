from pathlib import Path
import struct

src = Path("extracted/Counter/NA_1501_Btl_Counter.uasset")
dst = Path("output/NA_1501_Btl_Counter.uasset")

data = bytearray(src.read_bytes())

offset = 0x2A8

old_size = struct.unpack_from("<Q", data, offset)[0]
new_size = 8566

print(f"SerialSize offset : 0x{offset:X}")
print(f"旧 SerialSize     : {old_size}")
print(f"新 SerialSize     : {new_size}")

# 安全检查，防止改错文件
if old_size != 10289:
    raise RuntimeError(
        f"0x{offset:X} 处不是预期的 10289，而是 {old_size}，停止修改！"
    )

struct.pack_into("<Q", data, offset, new_size)

dst.write_bytes(data)

# 再读回来验证
check = dst.read_bytes()
patched_size = struct.unpack_from("<Q", check, offset)[0]

print(f"写入后 SerialSize: {patched_size}")
print(f"输出文件: {dst}")
print(f"UAsset 大小: {len(check)} bytes")