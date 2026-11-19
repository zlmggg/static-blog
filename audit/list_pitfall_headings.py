# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

rows = json.loads(Path(r"D:\Develop\static-blog\audit\pages_raw.json").read_text(encoding="utf-8"))
# scan actual body headings for merged command pages
for r in rows:
    if r["type"] != "命令详解":
        continue
    text = (Path(r"D:\Develop\static-blog\docs") / r["path"]).read_text(encoding="utf-8", errors="replace")
    hs = [h[1].strip() for h in re.findall(r"^(#{2,3})\s+(.+)$", text, re.M)]
    interesting = [h for h in hs if re.search(r"坑|注意|排错|易错|踩|故障|问题|案例", h)]
    if interesting:
        print(r["path"], "|", "；".join(interesting))
