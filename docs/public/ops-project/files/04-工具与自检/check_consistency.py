#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项目文档一致性自检：台数、资源总账、EIP、hosts、禁用词。
在仓库根目录执行：python scripts/check_consistency.py
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

EXPECT_VMS = 37
EXPECT_EIPS = 6
EXPECT_CPU = 70
EXPECT_RAM = 103
EXPECT_DISK = 875

ok = True
report = []


def check(name, cond, detail=""):
    global ok
    report.append(("PASS" if cond else "FAIL", name, detail))
    if not cond:
        ok = False


def read(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ---------- 1. 规划表：台数与资源总账 ----------
plan = read("01-总览与规划/项目IP规划表.md")
rows = re.findall(r"^\|\s*(\d{3})\s*\|\s*`([^`]+)`\s*\|([^|]*)\|\s*(\d+)\s*\|\s*([\d.]+)\s*G\s*\|\s*([^|]*?)\s*\|",
                  plan, re.M)
check("规划表 VM 数", len(rows) == EXPECT_VMS, f"实际 {len(rows)}，期望 {EXPECT_VMS}")


def disk_gb(cell):
    cell = cell.replace("*", "").strip()
    m = re.match(r"(\d+)×(\d+)\s*G", cell)
    if m:
        return int(m.group(1)) * int(m.group(2))
    m = re.match(r"([\d.]+)\s*G", cell)
    return float(m.group(1)) if m else 0


cpu = sum(int(r[3]) for r in rows)
ram = sum(float(r[4]) for r in rows)
disk = sum(disk_gb(r[5]) for r in rows)
check("vCPU 合计", cpu == EXPECT_CPU, f"{cpu} / {EXPECT_CPU}")
check("内存合计", ram == EXPECT_RAM, f"{ram}G / {EXPECT_RAM}G")
check("磁盘合计", disk == EXPECT_DISK, f"{disk}G / {EXPECT_DISK}G")

# 总账表里声明的数字要和明细一致
m = re.search(r"\|\s*vCPU\s*\|\s*(\d+)\s*\|", plan)
check("总账 vCPU 与明细一致", m and int(m.group(1)) == cpu, m.group(1) if m else "未找到")
m = re.search(r"\|\s*内存\s*\|\s*(\d+)\s*G\s*\|", plan)
check("总账 内存 与明细一致", m and int(m.group(1)) == ram, m.group(1) if m else "未找到")
m = re.search(r"\|\s*磁盘（虚拟）\s*\|\s*(\d+)\s*G\s*\|", plan)
check("总账 磁盘 与明细一致", m and int(m.group(1)) == disk, m.group(1) if m else "未找到")

# ---------- 2. EIP 条数 ----------
eips = re.findall(r"^(\d{3})\s+#", plan, re.M)
check("EIP 条数", len(eips) == EXPECT_EIPS, f"{len(eips)} 条：{','.join(eips)}")

# ---------- 3. inventory ----------
inv = read("04-工具与自检/ansible/inventory.ini")
hosts = re.findall(r"^[\w-]+\s+ansible_host=", inv, re.M)
check("inventory 主机数", len(hosts) == EXPECT_VMS, f"{len(hosts)} / {EXPECT_VMS}")
check("inventory 含 jumpserver", "jumpserver" in inv)

# ---------- 4. 初始化脚本 hosts ----------
sh = read("03-集群部署/p0-node-init.sh")
block = re.search(r"^# lab-hosts-begin$(.*?)^# lab-hosts-end$", sh, re.S | re.M)
entries = re.findall(r"^10\.0\.0\.\d+", block.group(1), re.M) if block else []
check("init 脚本 hosts 条数", len(entries) == EXPECT_VMS, f"{len(entries)} / {EXPECT_VMS}")
check("init 脚本含 jumpserver", "10.0.0.103" in sh)
check("init 脚本不含 VIP 记录", "10.0.0.119" not in sh)

# ---------- 5. 禁用词（历史遗留） ----------
forbidden = {
    "36 台": "项目已是 37 台",
    "437": "磁盘总量已恢复为 875G（thin 超配）",
    "ansible-01": "主控叫 bastion",
    "upstream-app.conf": "统一用 00-upstream.conf",
    "20 台 × 20G": "旧容量描述",
    "5 条 1:1 NAT": "EIP 已是 6 条",
}
files = [p for p in ROOT.rglob("*")
         if p.is_file() and p.suffix in {".md", ".sh", ".ini", ".py", ".yaml", ".conf"}
         and p.name != "check_consistency.py"]
for bad, why in forbidden.items():
    hits = []
    for f in files:
        if f.name == "check_consistency.py":
            continue
        try:
            if bad in f.read_text(encoding="utf-8"):
                hits.append(f.name)
        except Exception:
            pass
    check(f"禁用词 {bad!r}", not hits, f"命中：{hits}（{why}）" if hits else "")

# ---------- 6. 图表与文字版 ----------
arch = read("04-工具与自检/draw_arch.py")
check("架构图 37 台", "37 台" in arch)
check("架构图 6 条 EIP", "6 条：100 / 103 / 119 / 191 / 200 / 210" in arch)
check("架构图 JumpServer", "JumpServer" in arch)

text = read("01-总览与规划/项目架构-文字版.md")
for token in ["37 台", "103 G", "70 / 44", "875 G", "6 个 EIP", "JumpServer"]:
    check(f"文字版含 {token!r}", token in text)

# ---------- 输出 ----------
w = max(len(r[1]) for r in report) + 2
for state, name, detail in report:
    print(f"[{state}] {name:<{w}} {detail}")
print()
print("全部通过 [OK]" if ok else "存在不一致 [FAIL]")
sys.exit(0 if ok else 1)
