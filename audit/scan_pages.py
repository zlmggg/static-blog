# -*- coding: utf-8 -*-
"""扫描 docs 下全部 Markdown，输出页面盘点所需的原始指标。"""
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Develop\static-blog\docs")
OUT = Path(r"D:\Develop\static-blog\audit\pages_raw.json")

MARKERS = ["本文是", "从 0 到 1", "从0到1", "环境依据", "本篇定位", "本章自测", "官方文档"]
EVIDENCE = ["我", "踩坑", "实验", "复现", "线上", "事故", "故障", "阿里云", "ECS", "homelab", "X99", "Proxmox", "Docker", "Kubernetes", "K8s", "Nginx", "MySQL", "Redis", "Prometheus", "Ansible", "Jenkins"]


def parse_frontmatter(text: str):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end]
            body = text[end + 4:]
            title = None
            desc = None
            for line in fm.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip().strip('"').strip("'")
            return title, desc, body
    return None, None, text


def count_zh(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def classify_section(rel: str) -> str:
    if rel.startswith("guide/"):
        return "操作指南"
    if rel.startswith("reference/"):
        return "速查手册"
    if rel.startswith("cases/qa/"):
        return "问与答"
    if rel.startswith("cases/"):
        return "故障与排障"
    if rel.startswith("projects/"):
        return "我的项目"
    return "站点入口"


def page_type(rel: str) -> str:
    if rel in ("about.md", "roadmap.md", "index.md"):
        return "站点入口"
    if rel.startswith("projects/"):
        return "项目档案" if Path(rel).name != "index.md" else "项目入口"
    if rel == "cases/index.md":
        return "训练场入口"
    if rel == "cases/troubleshooting.md":
        return "排障记录入口"
    if rel.startswith("cases/qa/"):
        return "问答" if Path(rel).name != "index.md" else "问答入口"
    if rel.startswith("cases/t-"):
        return "训练案例"
    if rel.startswith("reference/"):
        name = Path(rel).name
        if name == "index.md":
            return "手册入口"
        if re.match(r"reference/cmd", rel):
            return "命令详解"
        return "速查总览"
    if rel.startswith("guide/"):
        return "指南"
    return "其他"


def main():
    rows = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if "/.vitepress/" in rel:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        title, desc, body = parse_frontmatter(text)
        h1 = re.search(r"^#\s+(.+)$", body, re.M)
        if not title:
            title = h1.group(1).strip() if h1 else path.stem
        headings = re.findall(r"^(#{2,3})\s+(.+)$", body, re.M)
        code_blocks = len(re.findall(r"```", body)) // 2
        tables = len(re.findall(r"^\|.+\|\s*$", body, re.M))
        zh = count_zh(body)
        total = len(re.sub(r"\s+", "", body))
        markers = {m: body.count(m) for m in MARKERS if body.count(m) > 0}
        # 真实/实验证据信号：只做计数，最终判断由人工规则完成
        evidence = {w: body.count(w) for w in EVIDENCE if body.count(w) > 0}
        rows.append({
            "path": rel,
            "section": classify_section(rel),
            "type": page_type(rel),
            "title": title,
            "description": desc or "",
            "chars": total,
            "zh_chars": zh,
            "headings": len(headings),
            "code_blocks": code_blocks,
            "tables": tables,
            "markers": markers,
            "marker_count": sum(markers.values()),
            "evidence": evidence,
            "first_text": re.sub(r"\s+", " ", body[:260]).strip(),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"pages={len(rows)} -> {OUT}")
    from collections import Counter
    print("sections:", dict(Counter(r["section"] for r in rows)))
    print("types:", dict(Counter(r["type"] for r in rows)))


if __name__ == "__main__":
    main()
