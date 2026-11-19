# -*- coding: utf-8 -*-
"""把 ops-checklists 并入 ops-templates，保留清单全文并移除独立入口。"""
import re
import shutil
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
ARCHIVE = Path(r"D:\Develop\static-blog\archive\merged-reference")
BACKUP = Path(r"D:\Develop\static-blog\audit\pre-merge-reference")

START = "<!-- merged-checklists:start -->"
END = "<!-- merged-checklists:end -->"


def strip_frontmatter(text: str):
    m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.S)
    return text[m.end():] if m else text


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    src = DOCS / "reference/ops-checklists.md"
    dst = DOCS / "reference/ops-templates.md"
    shutil.copy2(src, BACKUP / "ops-checklists.md")
    shutil.copy2(dst, BACKUP / "ops-templates.md")

    body = strip_frontmatter(src.read_text(encoding="utf-8"))
    body = re.sub(r"^#\s+.+\n", "", body, count=1, flags=re.M)
    body = re.sub(r"^##\s+", "### ", body, flags=re.M)
    body = body.replace("[运维文档模板](/reference/ops-templates)", "[运维文档模板](#)")
    body = body.strip()

    target = dst.read_text(encoding="utf-8")
    target = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\s*", "", target, flags=re.S)
    section = "\n".join([
        START,
        "## 运维检查清单",
        "",
        "> 上线前、日常巡检、应急、安全基线、容量、割接、灾备的逐项检查表，已并入本页。",
        "",
        body,
        "",
        END,
        "",
    ])
    dst.write_text(target.rstrip() + "\n\n" + section, encoding="utf-8")

    shutil.move(str(src), str(ARCHIVE / "ops-checklists.md"))
    (ARCHIVE / "README.md").write_text(
        "# 已合并的速查页\n\n`reference/ops-checklists.md` 已并入 `reference/ops-templates.md` 的「运维检查清单」。\n",
        encoding="utf-8",
    )

    # 全站旧链接
    for p in DOCS.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="replace")
        original = text
        text = text.replace("/reference/ops-checklists", "/reference/ops-templates#运维检查清单")
        text = text.replace("./ops-checklists", "./ops-templates#运维检查清单")
        if text != original:
            p.write_text(text, encoding="utf-8")
            print("links:", p.relative_to(DOCS).as_posix())


if __name__ == "__main__":
    main()
