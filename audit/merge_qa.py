# -*- coding: utf-8 -*-
"""把 7 篇问答页合并到对应领域页末尾的“常见问题 FAQ”。

答案保留全文，默认折叠，避免把领域页拉得过长。
"""
import re
import shutil
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
ARCHIVE = Path(r"D:\Develop\static-blog\archive\merged-qa")
BACKUP = Path(r"D:\Develop\static-blog\audit\pre-merge-faq")

MAP = {
    "cases/qa/linux.md": "guide/linux.md",
    "cases/qa/network.md": "guide/linux-network.md",
    "cases/qa/container.md": "guide/container.md",
    "cases/qa/database.md": "guide/data.md",
    "cases/qa/monitoring.md": "guide/monitor.md",
    "cases/qa/cloud.md": "guide/automation.md",
    "cases/qa/scenario.md": "cases/troubleshooting.md",
}
START = "<!-- merged-qa-faq:start -->"
END = "<!-- merged-qa-faq:end -->"


def strip_frontmatter(text: str):
    m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.S)
    return text[m.end():] if m else text


def parse_qa(text: str):
    text = strip_frontmatter(text)
    lines = text.splitlines()
    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    items = []
    section = ""
    current = None
    for line in lines:
        m_sec = re.match(r"^##\s+(.+)$", line)
        if m_sec:
            section = m_sec.group(1).strip()
            current = None
            continue
        m_q = re.match(r"^###\s+Q\d+[：:]\s*(.+)$", line)
        if m_q:
            current = {"section": section, "q": m_q.group(1).strip(), "body": []}
            items.append(current)
            continue
        if current is not None:
            current["body"].append(line)
    # 清掉答案末尾空行
    for it in items:
        while it["body"] and not it["body"][-1].strip():
            it["body"].pop()
    return title, items


def build_faq(title: str, items):
    lines = [
        START,
        "## 常见问题 FAQ",
        "",
        f"> {title}的高频问题已并入本页。默认只显示问题，点开查看完整答案。",
        "",
    ]
    last_section = None
    for idx, it in enumerate(items, 1):
        if it["section"] and it["section"] != last_section and it["section"] != "延伸阅读":
            lines += [f"### {it['section']}", ""]
            last_section = it["section"]
        q = it["q"].replace("**", "").strip()
        lines += [
            "<details>",
            f"<summary>Q{idx}：{q}</summary>",
            "",
        ]
        body = "\n".join(it["body"]).strip()
        lines += [body, "", "</details>", ""]
    lines += [END, ""]
    return "\n".join(lines)


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    for src_rel, dst_rel in MAP.items():
        src = DOCS / src_rel
        dst = DOCS / dst_rel
        shutil.copy2(dst, BACKUP / Path(dst_rel).name)
        title, items = parse_qa(src.read_text(encoding="utf-8"))
        if not items:
            print("no questions:", src_rel)
            continue
        faq = build_faq(title, items)
        target = dst.read_text(encoding="utf-8")
        target = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\s*", "", target, flags=re.S)
        target = target.rstrip() + "\n\n" + faq
        dst.write_text(target, encoding="utf-8")
        print(dst_rel, len(items))

    # 移动原问答页，含 index
    for p in sorted((DOCS / "cases/qa").glob("*.md")):
        rel = p.relative_to(DOCS).as_posix()
        dest = ARCHIVE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest))
        print("moved:", rel)
    (ARCHIVE / "README.md").write_text(
        "# 已合并的问答页\n\n"
        "这些页面原本位于 `docs/cases/qa/`，78 个问题已按业务域并入各领域页末尾的"
        "「常见问题 FAQ」，默认折叠；原页保留在这里，不参与站点构建。\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
