from pathlib import Path
import re

FILES = [
    Path(r"D:\Develop\static-blog\docs\projects\homelab\materials.md"),
    Path(r"D:\Develop\static-blog\docs\projects\homelab\tools.md"),
    Path(r"D:\Develop\static-blog\docs\projects\homelab\pve.md"),
]

def fix(text: str) -> str:
    # 直接下载的静态文件：用原生 <a>，避免 VitePress 把 .sh/.service 当成页面并追加 .html
    text = re.sub(
        r"\[`([^`]+)`\]\((/ops-project/files/[^)]+)\)",
        r'<a href="\2" download><code>\1</code></a>',
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\((/ops-project/files/[^)]+)\)",
        r'<a href="\2" download>\1</a>',
        text,
    )
    return text

for path in FILES:
    raw = path.read_text(encoding="utf-8")
    fixed = fix(raw)
    if fixed != raw:
        path.write_text(fixed, encoding="utf-8", newline="\n")
        print(f"FIXED {path.name}")
    else:
        print(f"NOCHANGE {path.name}")
