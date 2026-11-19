# -*- coding: utf-8 -*-
"""根据页面指标生成 V3 内容盘点表（初判，不修改正文）。"""
import json
import re
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import FormulaRule

ROOT = Path(r"D:\Develop\static-blog")
RAW = ROOT / "audit" / "pages_raw.json"
OUT = ROOT / "audit" / "sresec-content-inventory-v3.xlsx"

rows = json.loads(RAW.read_text(encoding="utf-8"))

# ---------------- 保留集合 ----------------
KEEP_GUIDES = {
    # 入口
    "guide/linux.md", "guide/services.md", "guide/data.md", "guide/container.md",
    "guide/monitor.md", "guide/automation.md", "guide/devops.md", "guide/aiops.md",
    "guide/architecture.md", "guide/career.md", "guide/blog.md",
    # Linux
    "guide/linux-process.md", "guide/linux-log.md", "guide/linux-storage.md",
    "guide/linux-security.md", "guide/linux-network.md",
    # 服务 / 数据
    "guide/services-web-nginx.md", "guide/services-lvs-keepalived.md",
    "guide/data-mysql.md", "guide/data-redis.md",
    # 监控
    "guide/monitor-prometheus-01-intro.md", "guide/monitor-prometheus-04-promql-exporter.md",
    "guide/monitor-prometheus-05-rules-alertmanager.md", "guide/monitor-elk.md", "guide/monitor-slo.md",
    # 容器
    "guide/container-docker.md", "guide/container-k8s-02-pod-service-discovery.md", "guide/container-helm.md",
    # 自动化 / 平台
    "guide/automation-ansible.md", "guide/automation-terraform.md", "guide/devops-cicd-advanced.md",
    # SRE / 专家
    "guide/expert-tough-cases.md", "guide/expert-security-incident.md",
    "guide/sre-incident.md", "guide/sre-capacity-dr.md",
    # 手记 / 职业 / AI / 架构
    "guide/blog-oncall-thriller.md", "guide/blog-war-stories.md", "guide/blog-field-rules.md",
    "guide/career-levels.md", "guide/aiops-agent-basics.md", "guide/architecture-capacity-sizing.md",
}

KEEP_CMDS = {
    # Linux 高频
    "reference/cmd/cd-pwd.md", "reference/cmd/ls.md", "reference/cmd/find.md", "reference/cmd/grep.md",
    "reference/cmd/awk.md", "reference/cmd/sed.md", "reference/cmd/tail.md", "reference/cmd/cp.md",
    "reference/cmd/mv.md", "reference/cmd/rm.md", "reference/cmd/chmod.md", "reference/cmd/ps.md",
    "reference/cmd/top.md", "reference/cmd/df.md", "reference/cmd/du.md",
    "reference/cmd/systemctl-journalctl.md", "reference/cmd/crontab.md", "reference/cmd/tar.md",
    "reference/cmd/ssh-rsync.md", "reference/cmd/lsof.md", "reference/cmd/strace.md",
    "reference/cmd/perf.md", "reference/cmd/logrotate.md", "reference/cmd/smartctl.md",
    # 网络
    "reference/cmd-net/ss.md", "reference/cmd-net/ip-addr-link.md", "reference/cmd-net/tcpdump.md",
    "reference/cmd-net/curl.md", "reference/cmd-net/dig.md", "reference/cmd-net/iptables.md",
    "reference/cmd/ethtool.md",
    # Docker
    "reference/cmd-docker/run.md", "reference/cmd-docker/build.md", "reference/cmd-docker/compose.md",
    "reference/cmd-docker/dockerfile.md", "reference/cmd-docker/logs.md",
    # kubectl
    "reference/cmd-kubectl/get.md", "reference/cmd-kubectl/describe.md", "reference/cmd-kubectl/logs.md",
    "reference/cmd-kubectl/apply-create.md",
    # Git
    "reference/cmd-git/workflow.md", "reference/cmd-git/reset-revert-restore.md", "reference/cmd-git/log-show.md",
    # 云原生
    "reference/cmd-cloudnative/kubectl-advanced.md", "reference/cmd-cloudnative/helm-troubleshoot.md",
    "reference/cmd-cloudnative/crictl.md",
}

KEEP_CASES = {
    "cases/t-nginx-502.md", "cases/t-nginx-504-timeout.md",
    "cases/t-mysql-replica-lag.md", "cases/t-mysql-deadlock.md", "cases/t-mysql-slow-query.md",
    "cases/t-redis-sentinel-failover.md", "cases/t-redis-memory-oom.md",
    "cases/t-docker-daemon-fail.md", "cases/t-docker-network-bridge.md", "cases/t-docker-storage-driver.md",
    "cases/t-k8s-pod-pending.md", "cases/t-k8s-crashloopbackoff.md",
    "cases/t-k8s-node-notready.md", "cases/t-k8s-etcd-failure.md",
    "cases/t-k8s-imagepullbackoff.md",
    "cases/t-dns-resolution-fail.md", "cases/t-tcp-retransmission.md",
    "cases/t-disk-space-full.md", "cases/t-process-d-state-hang.md", "cases/t-mining-trojan.md",
}

KEEP_REFERENCE = {
    "reference/index.md", "reference/linux-commands.md", "reference/network-commands.md",
    "reference/docker-commands.md", "reference/kubectl-commands.md", "reference/cloudnative-commands.md",
    "reference/git-commands.md", "reference/ai-prompts.md", "reference/ops-templates.md",
}

TEMPLATE_KEYS = ["本文是", "从 0 到 1", "从0到1", "环境依据", "本篇定位", "本章自测"]


def template_level(r):
    n = sum(r["markers"].get(k, 0) for k in TEMPLATE_KEYS)
    if r["type"] in ("命令详解", "速查总览"):
        return "高"
    if n >= 3:
        return "高"
    if n >= 1:
        return "中"
    return "低"


def evidence_level(r):
    p = r["path"]
    if p.startswith("projects/") and p != "projects/index.md":
        return "强"
    if p in ("about.md", "roadmap.md"):
        return "中"
    if p.startswith("guide/blog-"):
        return "中（复合案例）"
    if p.startswith("cases/t-"):
        return "中（实验复现）"
    if p.startswith("cases/qa/"):
        return "弱"
    if p.startswith("guide/arch-case-"):
        return "无（示例推演）"
    if p.startswith("guide/career-"):
        return "弱"
    if p.startswith("reference/") or p.startswith("guide/"):
        return "弱"
    return "弱"


def cmd_target(p):
    if p.startswith("reference/cmd-net/"):
        return "reference/network-commands.md（网络手册）"
    if p.startswith("reference/cmd-docker/"):
        return "reference/docker-commands.md（Docker 手册）"
    if p.startswith("reference/cmd-kubectl/"):
        return "reference/kubectl-commands.md（kubectl 手册）"
    if p.startswith("reference/cmd-git/"):
        return "reference/git-commands.md（Git 手册）"
    if p.startswith("reference/cmd-cloudnative/"):
        return "reference/cloudnative-commands.md（云原生手册）"
    return "reference/linux-commands.md（Linux 手册）"


def guide_merge_target(p):
    name = Path(p).name
    if p.startswith("guide/linux-"):
        return "guide/linux.md 或对应 Linux 核心篇"
    if p.startswith("guide/services-"):
        return "guide/services.md 或 guide/services-web-nginx.md"
    if p.startswith("guide/data-"):
        return "guide/data-mysql.md / data-redis.md 或 services 篇"
    if p.startswith("guide/monitor-prometheus-"):
        if "02" in name or "03" in name or "07" in name or "08" in name:
            return "guide/monitor-prometheus-04-promql-exporter.md"
        if "06" in name or "10" in name:
            return "guide/monitor-prometheus-05-rules-alertmanager.md"
        return "guide/monitor-prometheus-01-intro.md"
    if p.startswith("guide/monitor-zabbix"):
        return "guide/monitor.md（合并为一篇 Zabbix）"
    if p.startswith("guide/monitor-"):
        return "guide/monitor.md / monitor-slo.md"
    if p.startswith("guide/container-k8s-"):
        return "guide/container-k8s-02-pod-service-discovery.md"
    if p.startswith("guide/container-"):
        return "guide/container.md / container-docker.md / container-helm.md"
    if p.startswith("guide/automation-"):
        return "guide/automation-ansible.md / automation-terraform.md / devops-cicd-advanced.md"
    if p.startswith("guide/devops-"):
        return "guide/devops-cicd-advanced.md"
    if p.startswith("guide/aiops-"):
        return "guide/aiops-agent-basics.md"
    if p.startswith("guide/expert-"):
        return "guide/expert-tough-cases.md / expert-security-incident.md"
    if p.startswith("guide/sre-"):
        return "guide/sre-incident.md / sre-capacity-dr.md"
    if p.startswith("guide/career-"):
        return "guide/career-levels.md"
    if p.startswith("guide/blog-"):
        return "guide/blog.md（合并为一篇手记）"
    if p.startswith("guide/architecture-"):
        return "guide/architecture-capacity-sizing.md"
    if p.startswith("guide/config-"):
        return "reference/ops-templates.md"
    return "guide/linux.md（或归档）"


def classify(r):
    p = r["path"]
    t = r["type"]
    # 站点入口
    if p == "index.md":
        return "保留核心", "—", "首页入口；保留，但改为‘最近/精选/三条路径’，弱化 337 统计。", "P0"
    if p == "about.md":
        return "保留核心", "—", "身份、动机、联系方式，真人感强；保留并作为‘关于’入口。", "P0"
    if p == "roadmap.md":
        return "保留核心", "—", "阅读路径；保留，按新结构重写。", "P1"

    # 项目
    if p.startswith("projects/"):
        if p == "projects/index.md":
            return "保留核心", "—", "项目入口；保留，区分‘实战’与‘训练场’。", "P0"
        if p == "projects/site-blog.md":
            return "保留核心", "—", "真实项目；保留并更新 V3 口径（默认跟随系统、337 页、Gitee 私有等）。", "P0"
        if p == "projects/aliyun-deploy.md":
            return "保留核心", "—", "真实 ECS 部署记录；保留，补结果指标、截图与代价。", "P0"
        if p == "projects/homelab.md":
            return "保留核心", "—", "真实 Homelab；保留，补拓扑、成本与结果。", "P0"
        return "保留核心", "—", "项目页；保留。", "P0"

    # 案例入口
    if p == "cases/index.md":
        return "保留核心", "—", "训练场入口；保留，明确‘实验复现’，控制精选数量。", "P0"
    if p == "cases/troubleshooting.md":
        return "保留核心", "—", "日常排障记录；保留，作为短笔记流。", "P1"

    # 问答
    if p == "cases/qa/index.md":
        return "归档", "取消独立问答入口", "独立问答与 guide/reference 重叠；建议取消入口，FAQ 并入手册。", "P2"
    if p.startswith("cases/qa/"):
        return "合并", "对应手册/指南的 FAQ 节", "78 问与指南、命令页重复；合并为每本手册的 FAQ，保留 10–15 个高频问题。", "P1"

    # 训练案例
    if p.startswith("cases/t-"):
        if p in KEEP_CASES:
            return "保留深化", "—", "实验复现训练案例，覆盖高频故障；保留并标注‘实验环境’，不作为线上事故证据。", "P1"
        return "归档", "training-archive（不主推）", "同类案例已覆盖，边际价值低；归档到训练案例库，退出主导航与首页统计。", "P2"

    # 速查
    if p in KEEP_REFERENCE:
        if p == "reference/index.md":
            return "保留核心", "—", "手册入口；保留，收敛为 6–8 本手册。", "P0"
        if p == "reference/ops-templates.md":
            return "保留核心", "—", "模板实用；保留，吸收 ops-checklists。", "P1"
        return "保留核心", "—", "领域速查入口；保留，承接被合并的单命令页。", "P1"
    if p == "reference/ops-checklists.md":
        return "合并", "reference/ops-templates.md", "与模板/清单页重叠；合并为一份‘运维模板与清单’。", "P1"
    if p.startswith("reference/cmd"):
        if p in KEEP_CMDS:
            return "保留深化", "—", "高频/进阶独立命令页；保留，补真实排障例与版本差异。", "P1"
        return "合并", cmd_target(p), "单命令页与领域速查重复；保留独有坑点，合并进对应手册，原页移除/重定向。", "P1"

    # 指南
    if p.startswith("guide/"):
        if p in KEEP_GUIDES:
            if p in {
                "guide/linux.md", "guide/services.md", "guide/data.md", "guide/container.md",
                "guide/monitor.md", "guide/automation.md", "guide/devops.md", "guide/aiops.md",
                "guide/architecture.md", "guide/career.md", "guide/blog.md"
            }:
                return "保留核心", "—", "分区入口；保留，按新结构收敛子页。", "P1"
            if p.startswith("guide/blog-"):
                return "保留深化", "—", "第一人称叙事/经验；保留，但标注‘复合案例’，不作为亲历证据。", "P1"
            if p.startswith("guide/arch-case-"):
                return "归档", "—", "示例架构推演，未声明为本人项目；不构成能力证据，归档。", "P2"
            return "保留深化", "—", "核心主题；保留，补真实环境、决策、代价与结果。", "P1"

        if p.startswith("guide/arch-case-"):
            return "归档", "architecture-cases-archive", "示例架构推演，规模数字与案例均非本人项目；不构成能力证据，归档。", "P2"
        if p.startswith("guide/architecture-"):
            return "合并", "guide/architecture-capacity-sizing.md", "与容量/高可用主题重叠；合并为一篇‘架构与容量’。", "P1"
        if p.startswith("guide/opsdev") or p == "guide/opsdev.md":
            return "归档", "devdev-archive", "与 devdev 分区重复的入口页；归档。", "P2"
        if p.startswith("guide/devdev-"):
            return "归档", "devdev-archive", "自研平台教程，非本人项目证据；归档，保留少量真实平台经验。", "P2"
        if p.startswith("guide/config-"):
            return "合并", "reference/ops-templates.md", "配置模板与运维模板页重叠；合并。", "P1"
        if p.startswith("guide/blog-"):
            return "合并", "guide/blog.md（手记合集）", "同类手记；合并到一篇合集，保留最好的叙事。", "P1"
        if p.startswith("guide/career-"):
            return "合并", "guide/career-levels.md", "职业建议与能力篇重叠；合并为一篇，去掉求职导向。", "P1"
        if p.startswith("guide/aiops-"):
            return "合并", "guide/aiops-agent-basics.md", "AI 运维内容重复；合并为一篇入门 + 一篇实践。", "P1"
        if p.startswith("guide/expert-"):
            return "合并", "guide/expert-tough-cases.md / expert-security-incident.md", "与疑难/安全篇重叠；合并。", "P1"
        if p.startswith("guide/sre-"):
            return "合并", "guide/sre-incident.md / sre-capacity-dr.md", "与事故/容量篇重叠；合并。", "P1"
        if p.startswith("guide/monitor-"):
            return "合并", guide_merge_target(p), "Prometheus/Zabbix/监控主题重复；合并为更短的系列。", "P1"
        if p.startswith("guide/container-"):
            return "合并", guide_merge_target(p), "K8s/Docker 系列重复；合并为 3–4 篇核心笔记。", "P1"
        if p.startswith("guide/services-"):
            return "合并", guide_merge_target(p), "服务主题重复；合并到 Nginx/服务入口。", "P1"
        if p.startswith("guide/data-"):
            return "合并", guide_merge_target(p), "数据/中间件主题重复；合并到 MySQL/Redis/服务入口。", "P1"
        if p.startswith("guide/linux-"):
            return "合并", guide_merge_target(p), "Linux 子主题重复；合并到 4–5 篇核心笔记或命令手册。", "P1"
        if p.startswith("guide/automation-"):
            return "合并", guide_merge_target(p), "自动化主题重复；合并到 Ansible/Terraform/CI-CD。", "P1"
        if p.startswith("guide/devops-"):
            return "合并", guide_merge_target(p), "DevOps 主题重复；合并到 CI/CD 与密钥篇。", "P1"
        return "归档", "guide-archive", "主题宽泛、模板句密集、无个人环境；归档，不占主导航。", "P2"

    return "归档", "archive", "未归类页面；归档待核。", "P2"


data = []
for r in rows:
    action, target, reason, priority = classify(r)
    data.append({
        **r,
        "action": action,
        "target": target,
        "reason": reason,
        "priority": priority,
        "template": template_level(r),
        "evidence": evidence_level(r),
    })

print("actions:", Counter(d["action"] for d in data))
print("sections:", Counter(d["section"] for d in data))
print("keep guides:", len([d for d in data if d["path"] in KEEP_GUIDES]))
print("keep cmds:", len([d for d in data if d["path"] in KEEP_CMDS]))
print("keep cases:", len([d for d in data if d["path"] in KEEP_CASES]))

# 生成工作簿
wb = Workbook()


def style_sheet(ws, header_row=1, freeze="A2", autofilter=True):
    ws.freeze_panes = freeze
    if autofilter:
        ws.auto_filter.ref = ws.dimensions
    for cell in ws[header_row]:
        cell.fill = PatternFill("solid", fgColor="1F3864")
        cell.font = Font(name="微软雅黑", bold=True, color="FFFFFF", size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin = Side(style="thin", color="D9E2F3")
    for row in ws.iter_rows(min_row=header_row, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
        for cell in row:
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = Border(bottom=thin)
    ws.row_dimensions[header_row].height = 30
    ws.sheet_view.showGridLines = False


# 总览
ws = wb.active
ws.title = "总览"
ws["A1"] = "sresec.com · V3 内容盘点与收敛建议"
ws["A1"].font = Font(name="微软雅黑", bold=True, size=18, color="1F3864")
ws.merge_cells("A1:F1")
ws["A2"] = "口径：337 个 Markdown 页面；本表只做初判，不修改正文，不构成删除授权。归档页先保留文件，后续统一 301/410。"
ws["A2"].font = Font(name="微软雅黑", size=10, color="666666")
ws.merge_cells("A2:F2")

summary_rows = [
    ("指标", "数值", "说明"),
    ("总页数", len(data), "337 个 md（不含 .vitepress）"),
    ("操作指南", len([d for d in data if d["section"] == "操作指南"]), "115 页；目标 11 个入口 + 约 30 篇核心"),
    ("速查手册", len([d for d in data if d["section"] == "速查手册"]), "155 页；其中 145 个命令详解"),
    ("故障与排障", len([d for d in data if d["section"] == "故障与排障"]), "52 页；含 50 个训练案例"),
    ("问与答", len([d for d in data if d["section"] == "问与答"]), "8 页；78 问，建议并入手册 FAQ"),
    ("我的项目", len([d for d in data if d["section"] == "我的项目"]), "4 页；真实证据核心"),
    ("站点入口", len([d for d in data if d["section"] == "站点入口"]), "首页 / 关于 / 学习路线"),
    ("", "", ""),
    ("建议动作", "页数", "含义"),
]
for action in ["保留核心", "保留深化", "合并", "归档", "删除"]:
    summary_rows.append((action, len([d for d in data if d["action"] == action]), {
        "保留核心": "身份、项目、入口与核心手册",
        "保留深化": "精选训练案例、核心指南、高频命令",
        "合并": "同主题多页合并，原页 301/移除",
        "归档": "保留文件但不展示、不进主导航",
        "删除": "重复入口/空壳；本轮未实际删除",
    }[action]))

start_row = 4
for i, (a, b, c) in enumerate(summary_rows):
    ws.cell(start_row + i, 1, a)
    ws.cell(start_row + i, 2, b)
    ws.cell(start_row + i, 3, c)
    if i == 0 or a == "建议动作":
        for col in range(1, 4):
            ws.cell(start_row + i, col).fill = PatternFill("solid", fgColor="D9E2F3")
            ws.cell(start_row + i, col).font = Font(name="微软雅黑", bold=True, color="1F3864")

ws["A18"] = "建议的目标结构"
ws["A18"].font = Font(name="微软雅黑", bold=True, size=12, color="1F3864")
target_text = [
    "开始：关于 / 学习路线 / 最近在做什么（Now）",
    "实战档案：5–8 个真实项目与故障，必须有结果、代价、截图/拓扑",
    "手册：6–8 本（Linux、网络、Docker、K8s、Git、数据库、监控、云原生）",
    "手记：按时间/标签的短笔记流，保留第一人称与不确定性",
    "训练场：15–20 个最佳实验案例，明确标注‘实验复现’，不冒充线上事故",
]
for i, text in enumerate(target_text, 19):
    ws.cell(i, 1, "• " + text)
    ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=6)
    ws.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="center")

ws["A25"] = "执行顺序（先内容，后视觉）"
ws["A25"].font = Font(name="微软雅黑", bold=True, size=12, color="1F3864")
steps = [
    "1. 冻结新增页面：先不再生产新教程，避免一边砍一边长。",
    "2. 先处理 145 个命令页：保留 40–46 个高频/进阶页，其余合并进 6 本手册。",
    "3. 合并问答与指南：78 问压到 10–15 个 FAQ；Prometheus 10 篇压到 4–5 篇。",
    "4. 精选训练案例：50 个保留 15–20 个，其余归档，不再计入首页主统计。",
    "5. 重写核心 20 页：按‘我当时遇到什么→误判→验证→代价→改变’重写，删模板句。",
    "6. 最后改首页/导航：从‘337 篇’改为‘3 个真实项目 + 8 本手册 + 最新笔记’。",
]
for i, text in enumerate(steps, 26):
    ws.cell(i, 1, text)
    ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=6)
    ws.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="center")

ws.column_dimensions["A"].width = 26
ws.column_dimensions["B"].width = 10
ws.column_dimensions["C"].width = 70
ws.column_dimensions["D"].width = 12
ws.column_dimensions["E"].width = 12
ws.column_dimensions["F"].width = 12

# 页面盘点
ws2 = wb.create_sheet("页面盘点")
headers = ["序号", "分区", "页面路径", "标题", "类型", "字数", "模板痕迹", "真实证据", "建议动作", "建议去向", "理由", "优先级", "描述"]
ws2.append(headers)
for i, d in enumerate(sorted(data, key=lambda x: (x["section"], x["action"], x["path"])), 1):
    ws2.append([
        i, d["section"], d["path"], d["title"], d["type"], d["chars"], d["template"],
        d["evidence"], d["action"], d["target"], d["reason"], d["priority"], d["description"],
    ])

widths = {"A": 6, "B": 12, "C": 46, "D": 34, "E": 14, "F": 8, "G": 8, "H": 12, "I": 12, "J": 38, "K": 54, "L": 8, "M": 60}
for col, w in widths.items():
    ws2.column_dimensions[col].width = w
style_sheet(ws2, freeze="A2")
# 动作色阶（静态，便于阅读；不是条件格式）
fill_map = {
    "保留核心": "E2EFDA",
    "保留深化": "FFF2CC",
    "合并": "DDEBF7",
    "归档": "F2F2F2",
    "删除": "FCE4D6",
}
for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row, min_col=9, max_col=9):
    for cell in row:
        if cell.value in fill_map:
            cell.fill = PatternFill("solid", fgColor=fill_map[cell.value])
            cell.font = Font(name="微软雅黑", bold=True, size=10)

# 核心保留
ws3 = wb.create_sheet("核心保留")
headers3 = ["序号", "分区", "页面路径", "标题", "类型", "建议动作", "建议去向", "理由", "优先级"]
ws3.append(headers3)
keep = [d for d in data if d["action"].startswith("保留")]
for i, d in enumerate(sorted(keep, key=lambda x: (x["priority"], x["section"], x["path"])), 1):
    ws3.append([i, d["section"], d["path"], d["title"], d["type"], d["action"], d["target"], d["reason"], d["priority"]])
for col, w in {"A": 6, "B": 12, "C": 46, "D": 34, "E": 14, "F": 12, "G": 38, "H": 54, "I": 8}.items():
    ws3.column_dimensions[col].width = w
style_sheet(ws3)

# 合并映射
ws4 = wb.create_sheet("合并映射")
headers4 = ["序号", "页面路径", "标题", "建议动作", "合并到", "理由", "优先级"]
ws4.append(headers4)
merge = [d for d in data if d["action"] == "合并"]
for i, d in enumerate(sorted(merge, key=lambda x: (x["target"], x["path"])), 1):
    ws4.append([i, d["path"], d["title"], d["action"], d["target"], d["reason"], d["priority"]])
for col, w in {"A": 6, "B": 46, "C": 34, "D": 10, "E": 44, "F": 54, "G": 8}.items():
    ws4.column_dimensions[col].width = w
style_sheet(ws4)

# 归档清单
ws5 = wb.create_sheet("归档清单")
headers5 = ["序号", "分区", "页面路径", "标题", "类型", "建议动作", "去向", "理由", "优先级"]
ws5.append(headers5)
arch = [d for d in data if d["action"] in ("归档", "删除")]
for i, d in enumerate(sorted(arch, key=lambda x: (x["action"], x["section"], x["path"])), 1):
    ws5.append([i, d["section"], d["path"], d["title"], d["type"], d["action"], d["target"], d["reason"], d["priority"]])
for col, w in {"A": 6, "B": 12, "C": 46, "D": 34, "E": 14, "F": 10, "G": 30, "H": 54, "I": 8}.items():
    ws5.column_dimensions[col].width = w
style_sheet(ws5)

# 缺口与风险
ws6 = wb.create_sheet("缺口与风险")
ws6.append(["序号", "问题", "证据/现状", "影响", "建议"])
risks = [
    ("真实证据比例低", "337 页中只有 3 个项目页 + 少量真实踩坑；50 个案例明确写‘实验复现，不是线上事故’。", "招聘方/同行看不到能力证据，只看到知识整理。", "把项目页扩到 5–8 个，补结果、代价、截图、拓扑；训练场单独标注。"),
    ("四层重复", "145 命令页 + 6 本速查 + 115 指南 + 78 问答 + 50 案例；同一主题在四层出现。", "读者不知道哪篇权威；维护成本高。", "一主题一权威页；命令页合并进手册；问答并入手册 FAQ。"),
    ("模板化痕迹重", "280 处‘本文是’、265 处‘从 0 到 1’、129 处‘环境依据’、93 处‘本篇定位’。", "读三页就知道下一段；真人感弱。", "删模板句；每篇只留‘我遇到的具体问题、误判、代价、结果’。"),
    ("复合案例削弱‘真实’", "`blog-oncall-thriller`、`blog-war-stories`、`blog-go-live-night` 正文声明为第一人称复合案例。", "读者会误以为是亲历；与‘真实成长档案’冲突。", "保留为叙事，但显式标注‘复合案例’；不要放在‘实战证据’入口。"),
    ("架构案例非本人项目", "7 篇 `arch-case-*` 是示例规模/方案推演，未声明为本人项目。", "体量很大但不构成能力证据，反而稀释真实项目。", "归档；最多保留 1 篇并标‘示例推演’。"),
    ("首页以数量为主", "Hero 统计 337/145/50/25；没有‘最近在做什么/精选作品/三条路径’。", "传递‘量大’，不是‘可信’。", "首页改为‘最新 3 篇 + 2–3 个真实项目 + 3 条阅读路径’，统计移到关于页。"),
    ("长页缺就地导航", "awk 页 7,776px、Linux 问答页 12,125px；1180 宽下右侧大纲不显示。", "读者在长页中迷路，移动端更差。", "正文顶部加 TL;DR/本页目录；降低右侧大纲断点或提供页内 TOC。"),
    ("项目页口径过期", "`projects/site-blog.md` 仍写默认深色、325+ 篇、Gitee 公开 MIT、面经并入主站。", "与 V3 实际不一致，损害可信度。", "按 V3 实际更新：跟随系统、337 页、Gitee 私有、无独立面经入口。"),
    ("SEO 薄内容风险", "337 个页面中大量同模板、同主题内容；问答/命令/指南重叠。", "站点级 helpful content 信号可能被拖累。", "先合并/归档，再做 sitemap 与 301；不要继续加页。"),
    ("缺口：Now/结果指标", "没有‘最近在做什么’；项目页缺可量化结果（可用性、耗时、成本、故障恢复时间）。", "读者无法判断现在的能力与进展。", "新增 Now 页；每个项目补 3 个指标与 1 个失败点。"),
]
for i, (a, b, c, d) in enumerate(risks, 1):
    ws6.append([i, a, b, c, d])
for col, w in {"A": 6, "B": 24, "C": 70, "D": 50, "E": 60}.items():
    ws6.column_dimensions[col].width = w
style_sheet(ws6)

wb.save(OUT)
print("saved:", OUT)
print("keep total:", len(keep), "merge:", len(merge), "archive/delete:", len(arch))
