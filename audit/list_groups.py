# -*- coding: utf-8 -*-
import json
from pathlib import Path

rows = json.loads(Path(r"D:\Develop\static-blog\audit\pages_raw.json").read_text(encoding="utf-8"))
for sec in ["操作指南", "速查手册", "故障与排障", "问与答", "我的项目", "站点入口"]:
    print("\n### " + sec)
    for r in sorted([x for x in rows if x["section"] == sec], key=lambda x: (-x["chars"], x["path"])):
        if sec == "速查手册" and r["type"] == "命令详解":
            continue
        print(f'{r["path"]}\t{r["chars"]}\t{r["marker_count"]}\t{r["title"]}')
