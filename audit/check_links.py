# -*- coding: utf-8 -*-
import re
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
bad = []
for p in DOCS.rglob("*.md"):
    text = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", text):
        label, raw = m.group(1), m.group(2).strip()
        if raw.startswith(("http://", "https://", "mailto:", "#")):
            continue
        raw = raw.split("#", 1)[0].strip("<>")
        if not raw:
            continue
        if raw.startswith("/"):
            rel = raw.lstrip("/")
        else:
            rel = (p.parent.relative_to(DOCS) / raw).as_posix()
        rel = rel.replace("/./", "/")
        if rel.endswith(".html"):
            rel = rel[:-5]
        if rel.endswith("/"):
            rel += "index.md"
        elif not rel.endswith(".md"):
            rel += ".md"
        # 归一化 ../
        parts = []
        for part in rel.split("/"):
            if part == "..":
                if parts:
                    parts.pop()
            elif part not in ("", "."):
                parts.append(part)
        rel = "/".join(parts)
        if not (DOCS / rel).exists():
            bad.append((p.relative_to(DOCS).as_posix(), label[:50], raw))
print("bad links:", len(bad))
for row in bad[:80]:
    print(" | ".join(row))
