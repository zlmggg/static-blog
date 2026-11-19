# -*- coding: utf-8 -*-
"""用归档的原页重建 6 本手册的“命令坑点索引”，修正过长命令名与截断句。"""
import re
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
ARCHIVE = Path(r"D:\Develop\static-blog\archive\merged-commands")

TARGET = {
    "reference/cmd": "reference/linux-commands.md",
    "reference/cmd-net": "reference/network-commands.md",
    "reference/cmd-docker": "reference/docker-commands.md",
    "reference/cmd-kubectl": "reference/kubectl-commands.md",
    "reference/cmd-git": "reference/git-commands.md",
    "reference/cmd-cloudnative": "reference/cloudnative-commands.md",
}
START = "<!-- merged-command-pitfalls:start -->"
END = "<!-- merged-command-pitfalls:end -->"


def target_for(rel: str) -> str:
    for prefix, target in TARGET.items():
        if rel.startswith(prefix + "/"):
            return target
    raise ValueError(rel)


def command_label(title: str, stem: str) -> str:
    name = re.split(r"命令详解|详解", title, maxsplit=1)[0]
    name = name.strip(" ：:")
    name = name.replace("`", "").strip()
    if "：" in name:
        name = name.split("：", 1)[0].strip()
    if not name:
        name = stem.replace("-", " ")
    return name


def clean_item(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"^\s*(?:\d+\.|[-*])\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("|", "\\|")
    m = re.match(r"(.{15,190}?[。！？])", text)
    if m:
        return m.group(1).strip()
    if len(text) > 190:
        return text[:188].rstrip("，；、 ") + "…"
    return text


def extract_pitfalls(text: str):
    m = re.search(
        r"^##\s+[^\n]*(?:新手易错点|常见坑|常见报错与易错点|常见问题|控制面故障排查顺序)[^\n]*\n"
        r"(.*?)(?=^##\s|\Z)",
        text, re.M | re.S,
    )
    if not m:
        return []
    body = m.group(1)
    items = []
    for line in body.splitlines():
        if re.match(r"^\s*(?:\d+\.|[-*])\s+", line):
            item = clean_item(line)
            if len(item) >= 20:
                items.append(item)
        if len(items) >= 2:
            break
    if not items:
        para = " ".join(x.strip() for x in body.splitlines() if x.strip() and not x.strip().startswith(("|", "```", ">", ":::")))
        para = clean_item(para)
        if len(para) >= 20:
            items.append(para)
    return items


def official_url(text: str) -> str:
    m = re.search(r"^##\s*官方文档[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return ""
    urls = re.findall(r"https?://[^\s)>]+", m.group(1))
    return urls[0].rstrip(".,;") if urls else ""


def parse_title(text: str, fallback: str):
    m = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


def build_appendix(items):
    lines = [
        START,
        "## 命令坑点索引",
        "",
        "> 原先逐条拆开的单命令详解已合并到本手册；下面只保留每条命令最容易踩的坑，完整选项和示例不再单独成页。",
        "> 需要看某条命令的完整用法时，先在上方速查表找到它，再看本节对应行。",
        "",
        "| 命令 | 最容易踩的坑 | 官方文档 |",
        "|---|---|---|",
    ]
    for label, pitfall, url in sorted(items, key=lambda x: x[0].lower()):
        link = f"[官方]({url})" if url else "—"
        lines.append(f"| `{label}` | {pitfall} | {link} |")
    lines += ["", END, ""]
    return "\n".join(lines)


def main():
    appendices = {target: [] for target in TARGET.values()}
    for p in sorted(ARCHIVE.glob("reference/cmd*/**/*.md")):
        rel = p.relative_to(ARCHIVE).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        title = parse_title(text, p.stem)
        label = command_label(title, p.stem)
        pitfall = extract_pitfalls(text)
        pitfall = pitfall[0] if pitfall else "原页没有独立坑点段，待补。"
        appendices[target_for(rel)].append((label, pitfall, official_url(text)))

    for target, items in appendices.items():
        p = DOCS / target
        text = p.read_text(encoding="utf-8")
        appendix = build_appendix(items)
        text = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\s*", "", text, flags=re.S)
        positions = [text.find("## 官方文档"), text.find("## 相关问答")]
        positions = [x for x in positions if x >= 0]
        if positions:
            pos = min(positions)
            text = text[:pos] + appendix + "\n" + text[pos:]
        else:
            text = text.rstrip() + "\n\n" + appendix
        p.write_text(text, encoding="utf-8")
        print(target, len(items))


if __name__ == "__main__":
    main()
