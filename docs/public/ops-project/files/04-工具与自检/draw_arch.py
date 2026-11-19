# -*- coding: utf-8 -*-
"""Draw the merged architecture diagram and the PVE deployment diagram."""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "01-总览与规划"

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def font(size, bold=False):
    path = FONT_BOLD if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", size)


C_TEXT = "#1f2937"
C_MUTED = "#5b6472"
C_LINE = "#4b5563"

BANDS = {
    "edge":   ("#E8F0FE", "#5B7DB1"),
    "app":    ("#E6F4EA", "#3F7D52"),
    "data":   ("#FFF4E5", "#B26A00"),
    "cicd":   ("#F3E8FD", "#6A4C93"),
    "obs":    ("#FDECEC", "#A3423C"),
    "infra":  ("#ECEFF1", "#455A64"),
    "public": ("#FFF9C4", "#A68B00"),
}


def draw_box(d, rect, fill, outline, radius=18, width=3):
    d.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)


def draw_text(d, cx, cy, text, f, fill=C_TEXT, spacing=8):
    lines = text.split("\n")
    hs = []
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=f)
        hs.append(bb[3] - bb[1])
    total = sum(hs) + spacing * (len(lines) - 1)
    y = cy - total / 2
    for ln, h in zip(lines, hs):
        bb = d.textbbox((0, 0), ln, font=f)
        d.text((cx - (bb[2] - bb[0]) / 2, y - bb[1]), ln, font=f, fill=fill)
        y += h + spacing


def seg(d, p1, p2, color=C_LINE, width=3, dashed=False):
    x1, y1 = p1
    x2, y2 = p2
    if not dashed:
        d.line([p1, p2], fill=color, width=width)
        return
    dist = math.hypot(x2 - x1, y2 - y1)
    if dist == 0:
        return
    n = max(int(dist // 14), 1)
    for i in range(n):
        if i % 2 == 0:
            t1, t2 = i / n, min((i + 1) / n, 1)
            d.line([(x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1),
                    (x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2)],
                   fill=color, width=width)


def head_at(d, p1, p2, color, size=13):
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    a1, a2 = ang + math.radians(155), ang - math.radians(155)
    d.polygon([p2,
               (p2[0] + size * math.cos(a1), p2[1] + size * math.sin(a1)),
               (p2[0] + size * math.cos(a2), p2[1] + size * math.sin(a2))],
              fill=color)


def poly_arrow(d, pts, color=C_LINE, width=3, dashed=False):
    for i in range(len(pts) - 2):
        seg(d, pts[i], pts[i + 1], color, width, dashed)
    seg(d, pts[-2], pts[-1], color, width, dashed)
    head_at(d, pts[-2], pts[-1], color)


def arrow(d, p1, p2, color=C_LINE, width=3, dashed=False):
    poly_arrow(d, [p1, p2], color, width, dashed)


def band(d, rect, title, kind, title_size=28):
    fill, outline = BANDS[kind]
    d.rounded_rectangle(rect, radius=22, fill=fill, outline=outline, width=2)
    d.text((rect[0] + 20, rect[1] + 12), title, font=font(title_size, True), fill=outline)


def logical():
    W, H = 2400, 1660
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((60, 34), "在线教育平台 · 合并架构图（2.1 + 2.2 + 2.3 + 2.4）",
           font=font(46, True), fill="#111827")
    d.text((60, 96),
           "原型 100 台混合云 → 实验 37 台 PVE｜数据库/缓存/监控 + 自动化/CI-CD + Web/负载均衡 + Kubernetes/云 + 堡垒机",
           font=font(24), fill=C_MUTED)

    # ---------------- ① 接入层 ----------------
    band(d, (40, 160, 2360, 356), "① 接入层（业务入口）+ 运维入口", "edge")
    y0, y1 = 218, 330
    draw_box(d, (70, y0, 280, y1), "#FFFFFF", "#5B7DB1")
    draw_text(d, 175, (y0 + y1) / 2, "用户 APP/网页", font(23))
    draw_box(d, (310, y0 + 15, 440, y1 - 15), "#FFFFFF", "#5B7DB1")
    draw_text(d, 375, (y0 + y1) / 2, "DNS", font(24))
    draw_box(d, (470, y0, 780, y1), "#FFF9C4", "#A68B00")
    draw_text(d, 625, (y0 + y1) / 2, "公网入口 EIP\n192.168.10.119", font(21))
    draw_box(d, (810, y0, 1130, y1), "#FFFFFF", "#5B7DB1")
    draw_text(d, 970, (y0 + y1) / 2, "LVS + Keepalived（DR）\nVIP 10.0.0.119", font(21))
    draw_box(d, (1160, y0, 1480, y1), "#FFFFFF", "#5B7DB1")
    draw_text(d, 1320, (y0 + y1) / 2, "Nginx 七层 ×2\n静态 / 限流 / WAF\n蓝绿 upstream", font(20))

    d.line([(1510, 200), (1510, 336)], fill="#C5CDD8", width=2)
    d.text((1528, 176), "运维平面（人的入口）", font=font(19, True), fill="#6A4C93")
    draw_box(d, (1528, y0, 1900, y1), "#F3E8FD", "#6A4C93")
    draw_text(d, 1714, (y0 + y1) / 2, "JumpServer 堡垒机\nEIP .103 · 录像 / 审计", font(20))
    d.text((1918, 232), "SSH 代理 → 全部资产", font=font(18), fill=C_MUTED)
    d.text((1918, 262), "bastion 只做应急 + Ansible", font=font(18), fill=C_MUTED)

    for a, b in [((280, 274), (310, 274)), ((440, 274), (470, 274)),
                 ((780, 274), (810, 274)), ((1130, 274), (1160, 274))]:
        arrow(d, a, b)



    # ---------------- ② 应用层 ----------------
    band(d, (40, 386, 2360, 622), "② 应用层（蓝绿双组）", "app")
    y0, y1 = 448, 596
    b_app = (100, y0, 820, y1)
    b_nacos = (900, y0, 1500, y1)
    b_k8s = (1580, y0, 2180, y1)
    draw_box(d, b_app, "#FFFFFF", "#3F7D52")
    draw_text(d, 460, (y0 + y1) / 2, "SpringCloud 微服务\nblue-01/02（v1）  ·  green-01/02（v2）", font(24))
    draw_box(d, b_nacos, "#FFFFFF", "#3F7D52")
    draw_text(d, 1200, (y0 + y1) / 2, "Nacos 集群（3 副本）\n注册中心 + 配置中心 + 限流熔断", font(23))
    draw_box(d, b_k8s, "#FFFFFF", "#3F7D52")
    draw_text(d, 1880, (y0 + y1) / 2, "Kubernetes 3M + 2W\nIngress · HPA · 微服务 Pod", font(23))

    # Nginx -> 应用（走廊 y=370）
    poly_arrow(d, [(1320, 330), (1320, 370), (460, 370), (460, 446)])
    # 应用 <-> Nacos，K8s -> Nacos
    arrow(d, (822, 522), (898, 522))
    arrow(d, (1578, 522), (1502, 522))

    # ---------------- ③ 数据层 ----------------
    band(d, (40, 652, 2360, 888), "③ 缓存 / 数据库 / 存储 / 搜索", "data")
    y0, y1 = 714, 862
    draw_box(d, (100, y0, 560, y1), "#FFFFFF", "#B26A00")
    draw_text(d, 330, (y0 + y1) / 2, "MySQL 一主两从\nGTID + 半同步复制", font(23))
    draw_box(d, (620, y0, 1080, y1), "#FFFFFF", "#B26A00")
    draw_text(d, 850, (y0 + y1) / 2, "Redis 哨兵集群\n3 节点（redis + sentinel 同机）", font(22))
    draw_box(d, (1140, y0, 1600, y1), "#FFFFFF", "#B26A00")
    draw_text(d, 1370, (y0 + y1) / 2, "MinIO 集群\n3 节点 × 2 盘 · EC 4+2", font(22))
    draw_box(d, (1660, y0, 2180, y1), "#FFFFFF", "#B26A00")
    draw_text(d, 1920, (y0 + y1) / 2, "Elasticsearch 集群\n3 节点 · 课程搜索 + 日志存储", font(22))

    # 应用 -> 数据总线
    seg(d, (460, 598), (460, 700))
    seg(d, (330, 700), (1920, 700))
    for x in (330, 850, 1370, 1920):
        arrow(d, (x, 700), (x, 712))

    # ---------------- ④ CI/CD ----------------
    band(d, (40, 918, 1190, 1268), "④ 自动化 / CI·CD（1 master + 2 agent）", "cicd")
    cy0, cy1 = 1000, 1100
    draw_box(d, (70, cy0, 260, cy1), "#FFFFFF", "#6A4C93")
    draw_text(d, 165, (cy0 + cy1) / 2, "GitLab\n代码 + Runner", font(20))
    draw_box(d, (290, cy0, 600, cy1), "#FFFFFF", "#6A4C93")
    draw_text(d, 445, (cy0 + cy1) / 2, "Jenkins Master\n+ Agent ×2\ndocker / maven", font(19))
    draw_box(d, (630, cy0, 830, cy1), "#FFFFFF", "#6A4C93")
    draw_text(d, 730, (cy0 + cy1) / 2, "Harbor ×2\n双向复制", font(20))
    draw_box(d, (860, cy0, 1160, cy1), "#FFFFFF", "#6A4C93")
    draw_text(d, 1010, (cy0 + cy1) / 2, "Ansible ×3\n主控 / 备控 / 执行", font(20))
    arrow(d, (260, 1050), (288, 1050))
    arrow(d, (600, 1050), (628, 1050))
    arrow(d, (830, 1050), (858, 1050))
    d.text((70, 1132), "push → parallel 构建（maven + docker）→ 镜像扫描", font=font(19), fill=C_MUTED)
    d.text((70, 1162), "→ push Harbor → Ansible 部署（蓝绿 · 金丝雀 · 滚动）", font=font(19), fill=C_MUTED)

    # Ansible -> 应用（走廊 x=1110）
    poly_arrow(d, [(1010, 998), (1010, 910), (1110, 910), (1110, 630),
                   (560, 630), (560, 598)], color="#6A4C93", dashed=True)
    d.text((1128, 646), "部署", font=font(20), fill="#6A4C93")

    # ---------------- ⑤ 监控 / 日志 ----------------
    band(d, (1230, 918, 2360, 1268), "⑤ 监控 / 日志", "obs")
    m0, m1 = 972, 1052
    draw_box(d, (1260, m0, 1700, m1), "#FFFFFF", "#A3423C")
    draw_text(d, 1480, (m0 + m1) / 2, "Prometheus + Alertmanager", font(23))
    draw_box(d, (1900, m0, 2220, m1), "#FFFFFF", "#A3423C")
    draw_text(d, 2060, (m0 + m1) / 2, "Grafana", font(23))
    arrow(d, (1702, 1012), (1898, 1012))

    l0, l1 = 1085, 1165
    draw_box(d, (1260, l0, 1450, l1), "#FFFFFF", "#A3423C")
    draw_text(d, 1355, (l0 + l1) / 2, "Filebeat", font(21))
    draw_box(d, (1490, l0, 1700, l1), "#FFFFFF", "#A3423C")
    draw_text(d, 1595, (l0 + l1) / 2, "Logstash", font(21))
    draw_box(d, (1740, l0, 1950, l1), "#FFFFFF", "#A3423C")
    draw_text(d, 1845, (l0 + l1) / 2, "Elasticsearch", font(21))
    draw_box(d, (1990, l0, 2200, l1), "#FFFFFF", "#A3423C")
    draw_text(d, 2095, (l0 + l1) / 2, "Kibana", font(21))
    arrow(d, (1452, 1125), (1488, 1125))
    arrow(d, (1702, 1125), (1738, 1125))
    arrow(d, (1952, 1125), (1988, 1125))

    d.text((1250, 1192), "全网主机装 node_exporter / Filebeat，Prometheus 主动抓取", font=font(20), fill=C_MUTED)

    # ---------------- ⑥ 基础设施 ----------------
    band(d, (40, 1298, 2360, 1500), "⑥ 基础设施与网络（PVE 9.2 · 2696v4 22C/44T · 128G · 64G SSD + 512G NVMe）", "infra")
    iy0, iy1 = 1370, 1490
    draw_box(d, (80, iy0, 820, iy1), "#FFFFFF", "#455A64")
    draw_text(d, 450, (iy0 + iy1) / 2, "实验私网 vmbr1 10.0.0.0/24\n37 台 VM · 网关 10.0.0.1", font(22))
    draw_box(d, (880, iy0, 1560, iy1), "#FFF9C4", "#A68B00")
    draw_text(d, 1220, (iy0 + iy1) / 2, "公网区 192.168.10.0/24\nWindows .10 · PVE .30 · 路由器 .1", font(22))
    draw_box(d, (1620, iy0, 2300, iy1), "#FFFFFF", "#455A64")
    draw_text(d, 1960, (iy0 + iy1) / 2, "EIP 6 条：100 / 103 / 119 / 191 / 200 / 210\n1:1 NAT，VM 内部看不到公网 IP", font(21))

    # ---- 记忆口诀 ----
    d.rounded_rectangle((40, 1516, 2360, 1618), radius=18, fill="#FFFDE7", outline="#F9A825", width=3)
    d.text((66, 1530), "记忆口诀", font=font(24, True), fill="#8D6E00")
    d.text((210, 1532),
           "1 个入口 VIP　·　2 层代理（LVS 四层 + Nginx 七层）　·　3 类存储（MySQL / Redis / MinIO+ES）",
           font=font(22), fill="#4E342E")
    d.text((210, 1572),
           "4 组应用（blue 2 + green 2）　·　5 类入口（6 个 EIP）　·　6 段链路（接入 → 应用 → 数据 → CI/CD → 监控 → K8s）",
           font=font(22), fill="#4E342E")
    d.text((66, 1626), "实线 = 请求链路　　虚线 = 部署 / 配置下发", font=font(19), fill=C_MUTED)

    img.save(str(OUT_DIR / "架构图-逻辑.png"), "PNG")
    print("saved logical")


def deployment():
    W, H = 2400, 1560
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((60, 34), "实验集群部署图（37 台 · PVE 9.2）", font=font(46, True), fill="#111827")
    d.text((60, 96), "公网区 = 家庭 LAN 192.168.10.0/24；私网区 = vmbr1 10.0.0.0/24；EIP 由宿主机 1:1 NAT",
           font=font(24), fill=C_MUTED)

    band(d, (40, 150, 2360, 400), "公网区 192.168.10.0/24（路由器 .1 扮演互联网出口）", "public", 26)
    y0, y1 = 215, 350
    for x1, x2, txt in [
        (80, 420, "路由器\n192.168.10.1"),
        (460, 800, "Windows 工作站\n192.168.10.10"),
        (840, 1280, "PVE 宿主\n192.168.10.30"),
        (1320, 1760, "EIP 地址池\n192.168.10.100 – .254"),
        (1800, 2320, "对外入口\n.100 应急   .103 堡垒机   .119 VIP\n.191 监控   .200 GitLab   .210 Harbor"),
    ]:
        draw_box(d, (x1, y0, x2, y1), "#FFFFFF", "#A68B00")
        draw_text(d, (x1 + x2) / 2, (y0 + y1) / 2, txt, font(21))

    # PVE 大框
    d.rounded_rectangle((40, 430, 2360, 1500), radius=24, outline="#455A64", width=4, fill="#F7F9FA")
    d.text((1290, 452), "PVE 9.2 · E5-2696v4 22C/44T · 128G · 64G SSD + 512G NVMe · 192.168.10.30",
           font=font(26, True), fill="#37474F")

    draw_box(d, (80, 500, 1000, 590), "#E8F0FE", "#5B7DB1")
    draw_text(d, 540, 545, "vmbr0（桥接物理网卡）192.168.10.30/24", font(23))
    draw_box(d, (1040, 500, 2300, 590), "#FFF9C4", "#A68B00")
    draw_text(d, 1670, 545, "1:1 NAT（/etc/eip.map → eip.service）· ip_forward = 1", font(23))

    # 公网 -> 宿主
    arrow(d, (250, 352), (250, 498))
    arrow(d, (640, 352), (640, 498))
    arrow(d, (1670, 592), (1670, 638))

    draw_box(d, (80, 640, 2300, 1470), "#FFFFFF", "#455A64")
    d.text((108, 660), "vmbr1 实验私网 10.0.0.0/24 · 网关 10.0.0.1（NAT 出口）",
           font=font(24, True), fill="#37474F")

    groups = [
        ("管理 / 审计", "10.0.0.100–103", "1–4C / 1–8G", ["bastion（Ansible 主控 / DNS / 应急）", "ansible-02/03（备控 / 执行）", "jumpserver（堡垒机 / 审计）"], "EIP .100 / .103"),
        ("接入", "10.0.0.110–121", "1–2C / 1.5–2G", ["lvs-01/02  (+VIP .119)", "nginx-01/02"], "EIP .119 (VIP)"),
        ("应用（蓝绿）", "10.0.0.130–133", "2C / 3G", ["app-blue-01/02  (v1)", "app-green-01/02  (v2)"], "仅内网"),
        ("数据", "10.0.0.150–162", "1–2C / 1.5–3G", ["mysql-01/02/03", "redis-01/02/03"], "仅内网"),
        ("存储 / 搜索", "10.0.0.170–182", "1–2C / 1.5–4G", ["minio-01/02/03", "es-01/02/03  (+Logstash)"], "仅内网"),
        ("监控", "10.0.0.190–191", "2C / 2–3G", ["prom-01  (Prometheus)", "grafana-01  (+Kibana)"], "EIP .191"),
        ("CI/CD + 镜像", "10.0.0.200–211", "1–4C / 1.5–6G", ["gitlab-01 / jenkins-01", "agent-01/02（docker / maven）", "harbor-01/02（双向复制）"], "EIP .200 / .210"),
        ("Kubernetes", "10.0.0.220–231", "2–4C / 3–6G", ["k8s-m01/02/03  (control-plane)", "k8s-w01/02  (+Nacos 3 pod)"], "仅内网"),
    ]
    x0, y_top = 108, 710
    bw, bh, gap = 530, 330, 20
    for idx, (title, seg_txt, spec, lines, eip) in enumerate(groups):
        col, row = idx % 4, idx // 4
        x1 = x0 + col * (bw + gap)
        yy0 = y_top + row * (bh + 30)
        draw_box(d, (x1, yy0, x1 + bw, yy0 + bh), "#FFFFFF", "#78909C", radius=14)
        d.text((x1 + 18, yy0 + 16), title, font=font(26, True), fill="#263238")
        d.text((x1 + 18, yy0 + 58), seg_txt, font=font(22), fill=C_MUTED)
        d.text((x1 + 18, yy0 + 96), spec, font=font(20), fill="#6B7B8C")
        d.line([(x1 + 18, yy0 + 130), (x1 + bw - 18, yy0 + 130)], fill="#CFD8DC", width=2)
        ty = yy0 + 150
        for ln in lines:
            d.text((x1 + 18, ty), ln, font=font(22), fill="#37474F")
            ty += 42
        d.text((x1 + 18, yy0 + bh - 52), eip, font=font(21), fill="#A68B00")

    d.text((108, 1424), "EIP 只有 6 条；其余 31 台只在私网。VM 内部执行 ip a 看不到 192.168.10.x",
           font=font(21), fill=C_MUTED)

    img.save(str(OUT_DIR / "架构图-部署.png"), "PNG")
    print("saved deployment")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "logical"):
        logical()
    if which in ("all", "deployment"):
        deployment()
