# -*- coding: utf-8 -*-
import json
from pathlib import Path

rows = json.loads(Path(r"D:\Develop\static-blog\audit\pages_raw.json").read_text(encoding="utf-8"))
for r in sorted([x for x in rows if x["type"] == "命令详解"], key=lambda x: x["path"]):
    print(f'{r["path"]}\t{r["chars"]}\t{r["marker_count"]}\t{r["title"]}')
