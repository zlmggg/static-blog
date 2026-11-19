# -*- coding: utf-8 -*-
import json
from pathlib import Path

rows = json.loads(Path(r"D:\Develop\static-blog\audit\pages_raw.json").read_text(encoding="utf-8"))
paths = {r["path"] for r in rows}
sets = {}
# import sets from build script without executing build? simple parse by exec module? use regex? 
# Instead hardcode read the script file and exec its set literals is messy; just print known suspicious paths.
for p in [
    "reference/cmd-net/ethtool.md", "reference/cmd/ethtool.md",
    "guide/data.md", "guide/automation.md", "guide/devops.md", "guide/aiops.md",
    "guide/architecture.md", "guide/career.md",
]:
    print(p, p in paths)
print("cases count candidates:")
for p in sorted(x for x in paths if x.startswith("cases/t-")):
    print(p)
