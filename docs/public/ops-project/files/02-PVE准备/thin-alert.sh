#!/usr/bin/env bash
# ============================================================
# thin-alert.sh —— LVM thin 池使用率巡检与告警
#
# 放置：/usr/local/sbin/thin-alert.sh   (chmod 755)
# 配置：/etc/thin-alert.conf            (可选，脚本会自动 source)
# 定时：thin-alert.timer                (每 5 分钟)
#
# 行为：
#   - 读 thin 池的 data_percent（按实际写入算，不是虚拟分配）
#   - >= WARN(80) 记 warning，>= CRIT(90) 记 err
#   - 只在"状态发生变化"时告警，避免每 5 分钟刷屏
#   - 配了 WEBHOOK 就推一条（钉钉/企业微信的 text 格式）
#   - 有 node_exporter textfile 目录时，顺便写出 lvm_thin_data_percent 指标
# ============================================================
set -uo pipefail

CONF=/etc/thin-alert.conf
# shellcheck disable=SC1090
[ -f "$CONF" ] && . "$CONF"

VG=${VG:-nvme-vg}
POOL=${POOL:-nvme-thin}
WARN=${WARN:-80}
CRIT=${CRIT:-90}
WEBHOOK=${WEBHOOK:-}
STATE=${STATE:-/run/thin-alert.state}
TEXTFILE_DIR=${TEXTFILE_DIR:-/var/lib/node_exporter/textfile}

raw=$(lvs --noheadings --units % -o data_percent "$VG/$POOL" 2>/dev/null | tr -d ' %,')
if [ -z "$raw" ]; then
    logger -t thin-alert -p daemon.err "无法读取 $VG/$POOL 的 data_percent（池名或 VG 名不对？）"
    exit 0
fi
pct=${raw%.*}

# ---- 给 Prometheus 的 textfile collector 用 ----
if [ -d "$TEXTFILE_DIR" ]; then
    tmp="$TEXTFILE_DIR/.lvm_thin.prom.$$"
    printf 'lvm_thin_data_percent{vg="%s",pool="%s"} %s\n' "$VG" "$POOL" "$pct" > "$tmp" \
        && mv "$tmp" "$TEXTFILE_DIR/lvm_thin.prom"
fi

# ---- 分级 ----
level=ok
if [ "$pct" -ge "$CRIT" ]; then
    level=crit
elif [ "$pct" -ge "$WARN" ]; then
    level=warn
fi

prev=$(cat "$STATE" 2>/dev/null || echo unknown)
if [ "$level" = "$prev" ]; then
    exit 0                      # 状态没变，不重复告警
fi
echo "$level" > "$STATE"

case "$level" in
    crit) prio=err;     tag="CRIT" ;;
    warn) prio=warning; tag="WARN" ;;
    *)    prio=info;    tag="OK  " ;;
esac

msg="[PVE thin] ${VG}/${POOL} 使用率 ${pct}% —— ${tag}（预警 ${WARN}% / 告警 ${CRIT}%）"
logger -t thin-alert -p "daemon.${prio}" "$msg"
echo "$msg"

if [ -n "$WEBHOOK" ]; then
    curl -sS -m 5 -H 'Content-Type: application/json' \
        -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"${msg}\"}}" \
        "$WEBHOOK" >/dev/null 2>&1 || true
fi

exit 0
