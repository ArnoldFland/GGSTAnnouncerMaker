from pathlib import Path
import re

path = Path("extracted/Counter/NA_1501_Btl_Counter.uasset")
data = path.read_bytes()

strings = re.findall(rb"[ -~]{4,}", data)

for s in strings:
    print(s.decode("ascii", errors="ignore"))