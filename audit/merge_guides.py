# -*- coding: utf-8 -*-
"""把 60 篇同主题指南折叠合并进核心页，14 篇示例/教程归档。

目标：guide 目录从 115 篇降到 41 篇；合并内容默认折叠，保留全文。
"""
import html
import re
import shutil
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
ARCHIVE = Path(r"D:\Develop\static-blog\archive\merged-guides")
BACKUP = Path(r"D:\Develop\static-blog\audit\pre-merge-guides")

KEEP = {
    "guide/linux.md", "guide/services.md", "guide/data.md", "guide/container.md",
    "guide/monitor.md", "guide/automation.md", "guide/devops.md", "guide/aiops.md",
    "guide/architecture.md", "guide/career.md", "guide/blog.md",
    "guide/linux-process.md", "guide/linux-log.md", "guide/linux-storage.md",
    "guide/linux-security.md", "guide/linux-network.md",
    "guide/services-web-nginx.md", "guide/services-lvs-keepalived.md",
    "guide/data-mysql.md", "guide/data-redis.md",
    "guide/monitor-prometheus-01-intro.md", "guide/monitor-prometheus-04-promql-exporter.md",
    "guide/monitor-prometheus-05-rules-alertmanager.md", "guide/monitor-elk.md", "guide/monitor-slo.md",
    "guide/container-docker.md", "guide/container-k8s-02-pod-service-discovery.md", "guide/container-helm.md",
    "guide/automation-ansible.md", "guide/automation-terraform.md", "guide/devops-cicd-advanced.md",
    "guide/expert-tough-cases.md", "guide/expert-security-incident.md",
    "guide/sre-incident.md", "guide/sre-capacity-dr.md",
    "guide/blog-oncall-thriller.md", "guide/blog-war-stories.md", "guide/blog-field-rules.md",
    "guide/career-levels.md", "guide/aiops-agent-basics.md", "guide/architecture-capacity-sizing.md",
}

ARCHIVE_ONLY = {
    "guide/arch-case-app.md", "guide/arch-case-banking.md", "guide/arch-case-ecommerce.md",
    "guide/arch-case-game.md", "guide/arch-case-im.md", "guide/arch-case-microservice.md",
    "guide/arch-case-website.md",
    "guide/devdev-cli-bot.md", "guide/devdev-job-release.md", "guide/devdev-platform-cmdb.md",
    "guide/devdev-scheduler-api.md", "guide/devdev-ticket-dashboard.md",
    "guide/devdev-why-and-roadmap.md", "guide/opsdev.md",
}

START = "<!-- merged-guide-material:start -->"
END = "<!-- merged-guide-material:end -->"


def strip_frontmatter(text: str):
    m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.S)
    return text[m.end():] if m else text


def parse_meta(text: str, fallback: str):
    title = ""
    desc = ""
    m = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
    if m:
        title = m.group(1).strip()
    m = re.search(r"^description:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
    if m:
        desc = m.group(1).strip()
    body = strip_frontmatter(text)
    if not title:
        m = re.search(r"^#\s+(.+)$", body, re.M)
        title = m.group(1).strip() if m else fallback
    return title, desc, body


def make_detail(text: str, fallback: str):
    title, desc, body = parse_meta(text, fallback)
    body = re.sub(r"^#\s+.+\n", "", body, count=1, flags=re.M)
    # 折叠区里的标题降级，避免把右侧大纲撑爆
    body = re.sub(r"^##\s+", "#### ", body, flags=re.M)
    body = re.sub(r"^###\s+", "##### ", body, flags=re.M)
    body = body.strip()
    summary = html.escape(title)
    if desc:
        summary += " — " + html.escape(desc)
    return "\n".join([
        "<details>",
        f"<summary><strong>{summary}</strong></summary>",
        "",
        body,
        "",
        "</details>",
        "",
    ])


def target_for(rel: str) -> str:
    name = Path(rel).name
    if rel.startswith("guide/aiops-"):
        return "guide/aiops-agent-basics.md"
    if rel.startswith("guide/architecture-"):
        return "guide/architecture-capacity-sizing.md"
    if rel.startswith("guide/automation-") or rel in ("guide/automation-gitops.md", "guide/automation-jenkins.md"):
        return "guide/devops-cicd-advanced.md"
    if rel.startswith("guide/blog-"):
        return "guide/blog.md"
    if rel.startswith("guide/career-"):
        return "guide/career-levels.md"
    if rel.startswith("guide/config-"):
        return "reference/ops-templates.md"
    if rel.startswith("guide/container-k8s-"):
        return "guide/container-k8s-02-pod-service-discovery.md"
    if rel.startswith("guide/container-"):
        return "guide/container.md"
    if rel == "guide/data-mysql-advanced.md":
        return "guide/data-mysql.md"
    if rel.startswith("guide/data-"):
        return "guide/data.md"
    if rel.startswith("guide/devops-"):
        return "guide/devops-cicd-advanced.md"
    if rel.startswith("guide/expert-"):
        return "guide/expert-tough-cases.md"
    if rel.startswith("guide/linux-"):
        return "guide/linux.md"
    if rel.startswith("guide/monitor-prometheus-"):
        if any(x in name for x in ("02", "03", "07", "08")):
            return "guide/monitor-prometheus-04-promql-exporter.md"
        if any(x in name for x in ("06", "10")):
            return "guide/monitor-prometheus-05-rules-alertmanager.md"
        if "09" in name:
            return "guide/monitor-prometheus-01-intro.md"
    if rel.startswith("guide/monitor-"):
        return "guide/monitor.md"
    if rel.startswith("guide/services-"):
        return "guide/services.md"
    if rel == "guide/sre-chaos.md":
        return "guide/sre-incident.md"
    if rel == "guide/sre-python.md":
        return "guide/automation-ansible.md"
    raise ValueError(rel)


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    all_guides = sorted(p.relative_to(DOCS).as_posix() for p in (DOCS / "guide").glob("*.md"))
    merge = [x for x in all_guides if x not in KEEP and x not in ARCHIVE_ONLY]
    print("guides:", len(all_guides), "keep:", len(KEEP), "merge:", len(merge), "archive:", len(ARCHIVE_ONLY))

    targets = {}
    for rel in merge:
        targets.setdefault(target_for(rel), []).append(rel)

    for target, sources in sorted(targets.items()):
        dst = DOCS / target
        if not dst.exists():
            print("MISSING TARGET", target)
            continue
        backup = BACKUP / Path(target).name
        if not backup.exists():
            shutil.copy2(dst, backup)
        text = dst.read_text(encoding="utf-8")
        text = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\s*", "", text, flags=re.S)
        section = [START, "## 合并资料", "",
                   "> 原先单独成页的同主题内容已收进本页；默认折叠，点开看原页全文。", ""]
        for rel in sorted(sources):
            section.append(make_detail((DOCS / rel).read_text(encoding="utf-8"), Path(rel).stem))
        section += [END, ""]
        dst.write_text(text.rstrip() + "\n\n" + "\n".join(section), encoding="utf-8")
        print("merge", target, len(sources))

    # 移动所有非保留页
    for rel in all_guides:
        if rel in KEEP:
            continue
        src = DOCS / rel
        dest = ARCHIVE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    (ARCHIVE / "README.md").write_text(
        "# 已合并 / 归档的指南页\n\n"
        "60 篇同主题指南已折叠并入对应核心页的「合并资料」；14 篇示例架构、自研教程归档。"
        "原页保留在这里，不参与站点构建。\n",
        encoding="utf-8",
    )
    print("moved", len([x for x in all_guides if x not in KEEP]))


if __name__ == "__main__":
    main()
