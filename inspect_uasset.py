from pathlib import Path
import struct

path = Path("extracted/Counter/NA_1501_Btl_Counter.uasset")
data = path.read_bytes()

old_serial_size = 10289
new_serial_size = 8566

patterns = {
    "old uint32": struct.pack("<I", old_serial_size),
    "old uint64": struct.pack("<Q", old_serial_size),
}

print(f"UAsset size: {len(data)} bytes")
print(f"寻找旧 SerialSize: {old_serial_size}")
print()

for name, pattern in patterns.items():
    offsets = []
    start = 0

    while True:
        pos = data.find(pattern, start)
        if pos == -1:
            break

        offsets.append(pos)
        start = pos + 1

    print(name, "=>", [f"0x{x:X}" for x in offsets])

print()
print(f"新 SerialSize 应该是: {new_serial_size}")
print("uint32:", struct.pack("<I", new_serial_size).hex(" "))
print("uint64:", struct.pack("<Q", new_serial_size).hex(" "))