from pathlib import Path
import struct

# 文件路径
uexp_path = Path("extracted/Counter/NA_1501_Btl_Counter.uexp")
ogg_path = Path("output/UNI_Counter.ogg")
output_path = Path("output/NA_1501_Btl_Counter.uexp")

# 读取文件
uexp = uexp_path.read_bytes()
new_ogg = ogg_path.read_bytes()

# 找到原始 OGG
ogg_start = uexp.find(b"OggS")

if ogg_start == -1:
    raise RuntimeError("没有在 UEXP 中找到 OggS")

# 根据我们已经确认的结构：
# OggS 前 16 字节的位置保存了两个 little-endian 的 OGG 长度
size1_offset = ogg_start - 16
size2_offset = ogg_start - 12

old_size1 = struct.unpack_from("<I", uexp, size1_offset)[0]
old_size2 = struct.unpack_from("<I", uexp, size2_offset)[0]

print(f"OggS offset : 0x{ogg_start:X}")
print(f"旧长度字段 1: {old_size1}")
print(f"旧长度字段 2: {old_size2}")
print(f"新 OGG 长度 : {len(new_ogg)}")

# 安全检查
if old_size1 != old_size2:
    raise RuntimeError("两个长度字段不同，停止修改。")

old_ogg_end = ogg_start + old_size1

if old_ogg_end > len(uexp):
    raise RuntimeError("原 OGG 长度超出 UEXP 范围，停止修改。")

# 保存 OGG 后面的 UE4 数据
tail = uexp[old_ogg_end:]

print(f"OGG 后剩余 UE4 数据: {len(tail)} bytes")

# OGG 之前的数据
header = bytearray(uexp[:ogg_start])

# 写入新的 OGG 长度
struct.pack_into("<I", header, size1_offset, len(new_ogg))
struct.pack_into("<I", header, size2_offset, len(new_ogg))

# 重新组成 UEXP
new_uexp = bytes(header) + new_ogg + tail

output_path.write_bytes(new_uexp)

print()
print("完成！")
print(f"输出: {output_path}")
print(f"新 UEXP 大小: {len(new_uexp)} bytes")