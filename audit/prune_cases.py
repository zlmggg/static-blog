# -*- coding: utf-8 -*-
"""保留 20 个核心训练案例，其余 30 篇归档；同步 cases/index 与全站链接。"""
import re
import shutil
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
ARCHIVE = Path(r"D:\Develop\static-blog\archive\training-archive")
BACKUP = Path(r"D:\Develop\static-blog\audit\pre-prune-cases")

KEEP = {
    "t-nginx-502", "t-nginx-504-timeout", "t-mysql-replica-lag", "t-mysql-deadlock",
    "t-mysql-slow-query", "t-redis-sentinel-failover", "t-redis-memory-oom",
    "t-docker-daemon-fail", "t-docker-network-bridge", "t-docker-storage-driver",
    "t-k8s-pod-pending", "t-k8s-crashloopbackoff", "t-k8s-node-notready",
    "t-k8s-etcd-failure", "t-k8s-imagepullbackoff", "t-dns-resolution-fail",
    "t-tcp-retransmission", "t-disk-space-full", "t-process-d-state-hang", "t-mining-trojan",
}


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
        rel = (source.parent.relative_to(DOCS) / raw).as_posix()
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
    BACKUP.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DOCS / "cases/index.md", BACKUP / "index.md")

    all_cases = sorted(p.stem for p in (DOCS / "cases").glob("t-*.md"))
    archive = [x for x in all_cases if x not in KEEP]
    print("cases:", len(all_cases), "keep:", len([x for x in all_cases if x in KEEP]), "archive:", len(archive))

    # 过滤 cases/index.md 的表格行
    path = DOCS / "cases/index.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("共 50 篇", "共 20 篇")

    def filter_block(m):
        group, body = m.group(1), m.group(2)
        rows = []
        for line in body.splitlines():
            if line.startswith("|") and "/cases/" in line:
                ms = re.search(r"/cases/(t-[^)/]+)", line)
                if ms and ms.group(1) not in KEEP:
                    continue
            rows.append(line)
        kept = len([x for x in rows if x.startswith("|") and "/cases/" in x])
        return f"::: details {group}（{kept} 篇）\n" + "\n".join(rows) + "\n:::"

    text = re.sub(r"::: details ([^（\n]+)（\d+ 篇）\n(.*?)\n:::", filter_block, text, flags=re.S)
    path.write_text(text, encoding="utf-8")

    # 移动归档
    for stem in archive:
        src = DOCS / "cases" / (stem + ".md")
        dest = ARCHIVE / "cases" / (stem + ".md")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))

    # 全站链接：归档案例统一指向训练场入口
    archive_paths = {f"cases/{x}.md" for x in archive}
    for p in DOCS.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="replace")
        original = text

        def repl(m):
            raw = m.group(1)
            rel = resolve(p, raw)
            if rel in archive_paths:
                return "](/cases/)"
            return m.group(0)

        text = re.sub(r"\]\(([^)]+)\)", repl, text)
        if text != original:
            p.write_text(text, encoding="utf-8")
            print("links:", p.relative_to(DOCS).as_posix())

    # 首页 description 的 50 个案例改为 20
    index_md = DOCS / "index.md"
    s = index_md.read_text(encoding="utf-8")
    s = s.replace("50 个排障案例", "20 个排障案例")
    index_md.write_text(s, encoding="utf-8")

    (ARCHIVE / "README.md").write_text(
        "# 已归档的训练案例\n\n"
        "保留 20 个核心案例在 `docs/cases/`；其余 30 个同类复现案例归档到这里，"
        "不再参与站点构建，原链接在站内统一指向 `/cases/`。\n",
        encoding="utf-8",
    )
    print("done")


if __name__ == "__main__":
    main()
