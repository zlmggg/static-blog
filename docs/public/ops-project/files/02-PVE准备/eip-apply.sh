#!/usr/bin/env bash
# ============================================================
# eip-apply.sh —— 读取 /etc/eip.map，把私网 10.0.0.N 一对一映射为 192.168.10.N
#
# 放置：/usr/local/sbin/eip-apply.sh  (chmod 755)
# 配置：/etc/eip.map                  （一行一个末位，支持行内注释）
# 服务：/etc/systemd/system/eip.service（开机自动执行本脚本）
#
# 特性：
#   1. 支持行内注释： 100   # bastion
#   2. 幂等：每次清空自定义链重建，重复执行不会叠加规则
#   3. 自动清理：map 里删掉的条目，对应的 /32 地址也会被移除
#   4. 只动 PUB 段的 /32，不碰宿主机的 /24 管理地址
# ============================================================
set -euo pipefail

MAP="${MAP:-/etc/eip.map}"
PUB="${PUB:-192.168.10}"    # 公网段（家庭 LAN 示例）
PRIV="${PRIV:-10.0.0}"      # 私网段（实验 VPC）
DEV="${DEV:-vmbr0}"         # 公网侧网桥

log() { echo "[eip] $*"; }

# ---------- 1. 建链并挂到 PREROUTING / POSTROUTING ----------
iptables -t nat -N EIP-DNAT 2>/dev/null || true
iptables -t nat -N EIP-SNAT 2>/dev/null || true
iptables -t nat -F EIP-DNAT
iptables -t nat -F EIP-SNAT

iptables -t nat -C PREROUTING -i "$DEV" -j EIP-DNAT 2>/dev/null || \
    iptables -t nat -A PREROUTING -i "$DEV" -j EIP-DNAT
iptables -t nat -C POSTROUTING -o "$DEV" -j EIP-SNAT 2>/dev/null || \
    iptables -t nat -A POSTROUTING -o "$DEV" -j EIP-SNAT

# ---------- 2. 清理上一轮添加的 /32 地址（支持删除条目） ----------
mapfile -t _stale < <(
    ip -4 addr show dev "$DEV" 2>/dev/null |
    awk -v p="${PUB}." '$2 ~ "^"p"[0-9]+/32$" {print $2}'
)
for a in "${_stale[@]:-}"; do
    if [ -n "$a" ]; then
        ip addr del "$a" dev "$DEV" 2>/dev/null || true
    fi
done

# ---------- 3. 读映射表 ----------
if [ ! -f "$MAP" ]; then
    log "未找到 $MAP，跳过映射"
    exit 0
fi

count=0
while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"                 # 去掉行内注释
    line="${line//[[:space:]]/}"       # 去掉所有空白（含 Tab、回车）
    [ -z "$line" ] && continue

    if ! [[ "$line" =~ ^[0-9]{1,3}$ ]]; then
        log "跳过非法行：$line" >&2
        continue
    fi

    n=$((10#$line))                    # 按十进制解析，避免 0100 被当八进制
    if (( n < 2 || n > 254 )); then
        log "跳过越界号：$n" >&2
        continue
    fi

    ip addr add "${PUB}.${n}/32" dev "$DEV" 2>/dev/null || true
    iptables -t nat -A EIP-DNAT -d "${PUB}.${n}" -j DNAT --to-destination "${PRIV}.${n}"
    iptables -t nat -A EIP-SNAT -s "${PRIV}.${n}" -j SNAT --to-source "${PUB}.${n}"
    count=$((count + 1))
done < "$MAP"

log "已应用 ${count} 条映射：${PRIV}.N  <->  ${PUB}.N"
