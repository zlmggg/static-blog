# -*- coding: utf-8 -*-
"""把指向已合并/归档指南页的链接改到合并目标页或保留页。"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from merge_guides import KEEP, ARCHIVE_ONLY, target_for  # noqa: E402

DOCS = Path(r"D:\Develop\static-blog\docs")
ARCHIVE = Path(r"D:\Develop\static-blog\archive\merged-guides")

merge_map = {}
for p in sorted((ARCHIVE / "guide").glob("*.md")):
    rel = p.relative_to(ARCHIVE).as_posix()
    if rel not in ARCHIVE_ONLY:
        merge_map[rel] = target_for(rel)

archive_map = {rel: "guide/architecture-capacity-sizing.md" for rel in ARCHIVE_ONLY if rel.startswith("guide/arch-case-")}
archive_map.update({rel: "guide/devops.md" for rel in ARCHIVE_ONLY if rel.startswith(("guide/devdev-", "guide/opsdev"))})


def resolve(source: Path, raw: str):
    raw = raw.strip()
    if raw.startswith(("http://", "https://", "mailto:", "#")):
        return None
    raw = raw.split("#", 1)[0].strip("<>")
    if not raw:
        return None
    if raw.startswith("/"):
        rel = raw.lstrip("/")
    else:
        rel = str((source.parent.relative_to(DOCS) / raw).as_posix())
    if rel.endswith(".html"):
        rel = rel[:-5]
    if rel.endswith("/"):
        rel += "index.md"
    elif not rel.endswith(".md"):
        rel += ".md"
    parts = []
    for part in rel.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    return "/".join(parts)


def main():
    changed = []
    for p in DOCS.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="replace")
        original = text
        current = p.relative_to(DOCS).as_posix()

        def repl(m):
            raw = m.group(1)
            rel = resolve(p, raw)
            if not rel:
                return m.group(0)
            if rel in merge_map:
                dest = merge_map[rel]
                if dest == current:
                    return "](#合并资料)"
                return f"](/{dest[:-3]}#合并资料)"
            if rel in archive_map:
                return f"](/{archive_map[rel][:-3]})"
            return m.group(0)

        text = re.sub(r"\]\(([^)]+)\)", repl, text)
        if text != original:
            p.write_text(text, encoding="utf-8")
            changed.append(current)
    print("changed:", len(changed))
    for x in changed:
        print(x)


if __name__ == "__main__":
    main()
