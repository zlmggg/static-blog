# -*- coding: utf-8 -*-
"""把未保留的单命令页压缩进 6 本领域手册，并把原页移出 docs。

只移动、不删除：原页保存在 archive/merged-commands/ 下。
"""
import re
import shutil
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
ARCHIVE = Path(r"D:\Develop\static-blog\archive\merged-commands")
BACKUP = Path(r"D:\Develop\static-blog\audit\pre-merge-handbooks")
DEPLOY = Path(r"D:\Develop\static-blog\deploy\nginx")

# 与盘点表一致的 46 个保留页
KEEP_CMDS = {
    "reference/cmd/cd-pwd.md", "reference/cmd/ls.md", "reference/cmd/find.md", "reference/cmd/grep.md",
    "reference/cmd/awk.md", "reference/cmd/sed.md", "reference/cmd/tail.md", "reference/cmd/cp.md",
    "reference/cmd/mv.md", "reference/cmd/rm.md", "reference/cmd/chmod.md", "reference/cmd/ps.md",
    "reference/cmd/top.md", "reference/cmd/df.md", "reference/cmd/du.md",
    "reference/cmd/systemctl-journalctl.md", "reference/cmd/crontab.md", "reference/cmd/tar.md",
    "reference/cmd/ssh-rsync.md", "reference/cmd/lsof.md", "reference/cmd/strace.md",
    "reference/cmd/perf.md", "reference/cmd/logrotate.md", "reference/cmd/smartctl.md",
    "reference/cmd-net/ss.md", "reference/cmd-net/ip-addr-link.md", "reference/cmd-net/tcpdump.md",
    "reference/cmd-net/curl.md", "reference/cmd-net/dig.md", "reference/cmd-net/iptables.md",
    "reference/cmd/ethtool.md",
    "reference/cmd-docker/run.md", "reference/cmd-docker/build.md", "reference/cmd-docker/compose.md",
    "reference/cmd-docker/dockerfile.md", "reference/cmd-docker/logs.md",
    "reference/cmd-kubectl/get.md", "reference/cmd-kubectl/describe.md", "reference/cmd-kubectl/logs.md",
    "reference/cmd-kubectl/apply-create.md",
    "reference/cmd-git/workflow.md", "reference/cmd-git/reset-revert-restore.md", "reference/cmd-git/log-show.md",
    "reference/cmd-cloudnative/kubectl-advanced.md", "reference/cmd-cloudnative/helm-troubleshoot.md",
    "reference/cmd-cloudnative/crictl.md",
}

TARGET = {
    "reference/cmd": "reference/linux-commands.md",
    "reference/cmd-net": "reference/network-commands.md",
    "reference/cmd-docker": "reference/docker-commands.md",
    "reference/cmd-kubectl": "reference/kubectl-commands.md",
    "reference/cmd-git": "reference/git-commands.md",
    "reference/cmd-cloudnative": "reference/cloudnative-commands.md",
}
TARGET_TITLE = {
    "reference/linux-commands.md": "Linux 命令速查",
    "reference/network-commands.md": "网络命令速查",
    "reference/docker-commands.md": "Docker 命令速查",
    "reference/kubectl-commands.md": "kubectl 命令速查",
    "reference/git-commands.md": "Git 工作流速查",
    "reference/cloudnative-commands.md": "云原生命令速查",
}

START = "<!-- merged-command-pitfalls:start -->"
END = "<!-- merged-command-pitfalls:end -->"


def target_for(rel: str) -> str:
    for prefix, target in TARGET.items():
        if rel.startswith(prefix + "/"):
            return target
    raise ValueError(rel)


def command_label(title: str, stem: str) -> str:
    name = re.split(r"\s*命令详解", title, maxsplit=1)[0].strip()
    name = name.replace("`", "").strip()
    if not name:
        name = stem.replace("-", " ")
    return name


def clean_item(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"^\s*(?:\d+\.|[-*])\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("|", "\\|")
    # 取第一句，避免把整段复制过来
    m = re.match(r"(.{15,160}?[。！？；])", text)
    if m:
        text = m.group(1)
    return text.strip()


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
        if len(items) >= 3:
            break
    if not items:
        para = " ".join(x.strip() for x in body.splitlines() if x.strip() and not x.strip().startswith(("|", "```", ">", ":::")))
        para = clean_item(para)
        if len(para) >= 20:
            items.append(para)
    return items[:2]


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


def build_appendix(target: str, items):
    lines = [
        START,
        "## 命令坑点索引",
        "",
        f"> 原先逐条拆开的单命令详解已合并到本手册；下面的“坑点”来自原页，完整选项和示例不再单独成页。",
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


def insert_appendix(text: str, appendix: str):
    # 去掉旧版本，保证可重复执行
    text = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\s*", "", text, flags=re.S)
    positions = [
        text.find("## 官方文档"),
        text.find("## 相关问答"),
    ]
    positions = [p for p in positions if p >= 0]
    if positions:
        p = min(positions)
        return text[:p] + appendix + "\n" + text[p:]
    return text.rstrip() + "\n\n" + appendix


def resolve_link(source_file: Path, raw: str):
    raw = raw.strip()
    if raw.startswith(("http://", "https://", "mailto:", "#")):
        return None
    raw = raw.split("#", 1)[0].strip("<>")
    if not raw:
        return None
    if raw.startswith("/"):
        rel = raw.lstrip("/")
    else:
        rel = str((source_file.parent.relative_to(DOCS) / raw).as_posix())
    if rel.endswith(".html"):
        rel = rel[:-5]
    if rel.endswith("/"):
        rel += "index.md"
    elif not rel.endswith(".md"):
        rel += ".md"
    return rel


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    DEPLOY.mkdir(parents=True, exist_ok=True)

    command_pages = []
    for p in DOCS.glob("reference/cmd*/**/*.md"):
        rel = p.relative_to(DOCS).as_posix()
        if rel not in KEEP_CMDS:
            command_pages.append(rel)
    merged = sorted(command_pages)
    print("merged count:", len(merged))

    # 备份 6 本手册
    for target in TARGET_TITLE:
        src = DOCS / target
        shutil.copy2(src, BACKUP / Path(target).name)

    # 生成每本手册的坑点索引
    appendices = {target: [] for target in TARGET_TITLE}
    for rel in merged:
        p = DOCS / rel
        text = p.read_text(encoding="utf-8", errors="replace")
        title = parse_title(text, Path(rel).stem)
        label = command_label(title, Path(rel).stem)
        pitfalls = extract_pitfalls(text)
        if not pitfalls:
            pitfalls = ["原页没有独立的“新手易错点”段；完整示例已合并，本节保留命令名待补。"]
        appendices[target_for(rel)].append((label, pitfalls[0], official_url(text)))

    for target, items in appendices.items():
        p = DOCS / target
        text = p.read_text(encoding="utf-8")
        appendix = build_appendix(target, items)
        new = insert_appendix(text, appendix)
        p.write_text(new, encoding="utf-8")
        print("appendix:", target, len(items))

    # 全站链接改写：指向被合并页的链接，改为指向对应手册
    moved = {m: target_for(m) for m in merged}
    for p in DOCS.rglob("*.md"):
        rel_file = p.relative_to(DOCS).as_posix()
        if rel_file in moved:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        original = text

        def repl(match):
            label, raw = match.group(1), match.group(2)
            target = resolve_link(p, raw)
            if target in moved:
                dest = moved[target]
                if rel_file == dest:
                    return label
                return f"[{label}](/{dest[:-3]})"
            return match.group(0)

        text = re.sub(r"\[([^\]]*)\]\(([^)]+)\)", repl, text)
        if text != original:
            p.write_text(text, encoding="utf-8")
            print("links:", rel_file)

    # 移出 docs
    for rel in merged:
        src = DOCS / rel
        dst = ARCHIVE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
    (ARCHIVE / "README.md").write_text(
        "# 已合并的单命令页\n\n"
        "这些页面原本位于 `docs/reference/cmd*/`，内容已压缩进 6 本领域手册的"
        "「命令坑点索引」；原页移到这里保留，不再参与站点构建。\n",
        encoding="utf-8",
    )
    print("moved:", len(merged))

    # 生成 Nginx 301 配置（本地不生效，部署时 include）
    lines = ["# 单命令页合并后的 301 规则", "# 部署时在 nginx 配置中 include 本文件", ""]
    for rel, target in moved.items():
        url = "/" + rel[:-3]
        lines.append(f"location = {url} {{ return 301 /{target[:-3]}; }}")
        lines.append(f"location = {url}.html {{ return 301 /{target[:-3]}; }}")
    (DEPLOY / "command-redirects.conf").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("redirects:", DEPLOY / "command-redirects.conf")


if __name__ == "__main__":
    main()
