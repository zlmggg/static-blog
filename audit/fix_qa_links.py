# -*- coding: utf-8 -*-
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
MAP = {
    "/cases/qa/linux": "/guide/linux#常见问题-faq",
    "/cases/qa/network": "/guide/linux-network#常见问题-faq",
    "/cases/qa/container": "/guide/container#常见问题-faq",
    "/cases/qa/database": "/guide/data#常见问题-faq",
    "/cases/qa/monitoring": "/guide/monitor#常见问题-faq",
    "/cases/qa/cloud": "/guide/automation#常见问题-faq",
    "/cases/qa/scenario": "/cases/troubleshooting#常见问题-faq",
    "/cases/qa/": "/guide/linux#常见问题-faq",
}
for p in DOCS.rglob("*.md"):
    text = p.read_text(encoding="utf-8", errors="replace")
    original = text
    for old, new in MAP.items():
        text = text.replace(old, new)
    if text != original:
        p.write_text(text, encoding="utf-8")
        print(p.relative_to(DOCS).as_posix())
