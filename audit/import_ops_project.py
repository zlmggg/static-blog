from pathlib import Path
import re

SRC = Path(r"D:\workplace\运维项目")
DST = Path(r"D:\Develop\static-blog\docs\projects\homelab")
PUB = Path(r"D:\Develop\static-blog\docs\public\ops-project")

DST.mkdir(parents=True, exist_ok=True)
(DST / "practice").mkdir(parents=True, exist_ok=True)
(PUB / "files").mkdir(parents=True, exist_ok=True)


def sanitize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 家庭实验网段统一改成示例私网，避免真实家庭网段暴露
    text = text.replace("192.168.3.", "192.168.10.")
    text = re.sub(r"192\.168\.3(?!\d)", "192.168.10", text)
    # 原文里的本机目录路径改成站点附件目录说明
    text = text.replace(r"D:\workplace\运维项目\02-PVE准备", r".\ops-project-files\02-PVE准备")
    text = text.replace(r"D:\workplace\运维项目\03-集群部署", r".\ops-project-files\03-集群部署")
    text = text.replace(r"D:\workplace\运维项目", r".\ops-project-files")
    # 所有实验密码改成占位符；站点不保存密码
    text = re.sub(r"[A-Za-z0-9_.-]+@2026", "【实验密码】", text)
    text = text.replace("admin123", "【实验密码】")
    text = text.replace("密码 `admin`", "密码 `【首次登录密码】`")
    text = text.replace("`admin` / `admin`", "`admin` / `【首次登录密码】`")
    text = text.replace("账号 `admin`，密码 `admin`", "账号 `admin`，密码 `【首次登录密码】`")
    return text


MAP = {
    "00-操作规范.md": "/projects/homelab/rules",
    "00-索引.md": "/projects/homelab/",
    "00-资料清单.md": "/projects/homelab/materials",
    "项目IP规划表.md": "/projects/homelab/ip-plan",
    "项目架构-文字版.md": "/projects/homelab/architecture",
    "工作清单-物理机就绪后.md": "/projects/homelab/work-checklist",
    "10-实操/00-资料清单.md": "/projects/homelab/materials",
    "10-实操/README.md": "/projects/homelab/practice/",
    "02-PVE准备/PVE-AD3-部署手册.md": "/projects/homelab/pve",
    "03-集群部署/部署手册-P0-P1.md": "/projects/homelab/cluster",
    "05-参考/PVE虚拟机命令手册.md": "/projects/homelab/reference",
    "04-工具与自检/README.md": "/projects/homelab/tools",
    "01-总览与规划/项目架构-文字版.md": "/projects/homelab/architecture",
    "01-总览与规划/项目IP规划表.md": "/projects/homelab/ip-plan",
    "01-总览与规划/工作清单-物理机就绪后.md": "/projects/homelab/work-checklist",
}

PRACTICE = [
    "01-D0-装机与PVE初始化.md",
    "02-D1-P0管理平面.md",
    "03-D1-P1最小链路.md",
    "04-D1-P15堡垒机.md",
    "05-D2-P2-1数据层高可用.md",
    "06-D2-P2-2对象存储与搜索.md",
    "07-D2-P2-3蓝绿发布.md",
    "08-P3-0中间件Nacos与日志.md",
    "09-P3-1若依部署与MinIO.md",
    "10-P3-2若依接入ES.md",
    "11-P3-3若依蓝绿发布.md",
    "12-P4-K8s迁移.md",
    "13-P5-mall-swarm.md",
]
for name in PRACTICE:
    MAP[f"10-实操/{name}"] = f"/projects/homelab/practice/{name[:-3]}"


def rewrite_links(text: str) -> str:
    for old, new in MAP.items():
        for prefix in ("", "../", "./"):
            text = text.replace(f"({prefix}{old})", f"({new})")
            text = text.replace(f"(<{prefix}{old}>)", f"({new})")
    # 去掉会暴露原家庭网段拓扑的图片引用；站点用总览页的 Mermaid 图代替
    text = re.sub(r"!\[[^\]]*\]\(<?[^)]*架构图[^)]*\.png[^)]*>?\)", "", text)
    text = re.sub(r"\[[^\]]*架构图[^\]]*\]\(<?[^)]*架构图[^)]*\.png[^)]*>?\)", "架构图（见总览页）", text)
    return text


def copy_md(src_rel: str, dst_rel: str) -> None:
    src = SRC / src_rel
    if not src.exists():
        print(f"MISSING {src_rel}")
        return
    text = rewrite_links(sanitize(src.read_text(encoding="utf-8")))
    dst = DST / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8", newline="\n")
    print(f"MD  {src_rel} -> {dst_rel}")


for src_rel, dst_rel in [
    ("00-操作规范.md", "rules.md"),
    ("01-总览与规划/项目架构-文字版.md", "architecture.md"),
    ("01-总览与规划/项目IP规划表.md", "ip-plan.md"),
    ("01-总览与规划/工作清单-物理机就绪后.md", "work-checklist.md"),
    ("02-PVE准备/PVE-AD3-部署手册.md", "pve.md"),
    ("03-集群部署/部署手册-P0-P1.md", "cluster.md"),
    ("05-参考/PVE虚拟机命令手册.md", "reference.md"),
    ("10-实操/README.md", "practice/index.md"),
]:
    copy_md(src_rel, dst_rel)

for name in PRACTICE:
    copy_md(f"10-实操/{name}", f"practice/{name}")

# 脚本与配置作为可下载附件；内容同样脱敏
SCRIPT_DIRS = [
    "02-PVE准备",
    "03-集群部署",
    "04-工具与自检",
]
SCRIPT_SUFFIX = {".sh", ".service", ".timer", ".yaml", ".yml", ".conf", ".py", ".ini", ".cfg"}
for base in SCRIPT_DIRS:
    for src in (SRC / base).rglob("*"):
        if src.is_file() and src.suffix.lower() in SCRIPT_SUFFIX:
            rel = src.relative_to(SRC)
            dst = PUB / "files" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(sanitize(src.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
            print(f"FILE {rel}")

print("DONE")
