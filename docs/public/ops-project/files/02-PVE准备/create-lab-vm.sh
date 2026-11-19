#!/usr/bin/env bash
# ============================================================
# 按 VMID 创建实验虚拟机：私网 IP 末位 = VMID
#   例：create-lab-vm.sh 110  ->  10.0.0.110/24
# 用法：bash create-lab-vm.sh <vmid 100-254> [cores] [memMB] [diskGB]
# 环境变量：TEMPLATE_ID STORAGE BRIDGE GATEWAY NETPREFIX CIDR DNS1 CIUSER SSHKEY_FILE START
#
# 说明：VM 只配私网地址。需要"公网 IP"时，在宿主机用 /etc/eip.map + eip.service
#       做 1:1 NAT（手册 0.5），VM 本身不用改任何配置。
# ============================================================
set -euo pipefail

TEMPLATE_ID="${TEMPLATE_ID:-9000}"
STORAGE="${STORAGE:-nvme-lvm}"          # NVMe thin 池（见 PVE 手册 6.1）
BRIDGE="${BRIDGE:-vmbr1}"
GATEWAY="${GATEWAY:-10.0.0.1}"
NETPREFIX="${NETPREFIX:-10.0.0}"
CIDR="${CIDR:-24}"
DNS1="${DNS1:-223.5.5.5}"
CIUSER="${CIUSER:-ubuntu}"
SSHKEY_FILE="${SSHKEY_FILE:-/root/.ssh/id_ed25519.pub}"
START="${START:-1}"

die() { echo "[ERROR] $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "请用 root 执行"
command -v qm >/dev/null 2>&1 || die "未找到 qm，请在本机 PVE 上运行"

if [ $# -lt 1 ]; then
    cat >&2 <<EOF
用法: bash $0 <vmid 100-254> [cores] [memMB] [diskGB]

示例:
  bash $0 110                 # 2C/2G/20G -> 10.0.0.110
  bash $0 120 4 4096 40      # 4C/4G/40G -> 10.0.0.120

批量:
  for id in \$(seq 110 114); do bash $0 \$id 2 2048 20; sleep 2; done
EOF
    exit 1
fi

VMID="$1"
CORES="${2:-2}"
MEM="${3:-2048}"
DISK="${4:-20}"

[[ "$VMID" =~ ^[0-9]+$ ]] || die "VMID 必须是数字"
VMID=$((10#$VMID))                       # 去掉前导零，避免被当成八进制
(( VMID >= 100 && VMID <= 254 )) || die "VMID 必须在 100-254（最后一段即 IP）"
[[ "$CORES" =~ ^[0-9]+$ ]] || die "cores 必须是数字"
[[ "$MEM" =~ ^[0-9]+$ ]] || die "memMB 必须是数字"
[[ "$DISK" =~ ^[0-9]+$ ]] || die "diskGB 必须是数字"

qm status "$TEMPLATE_ID" >/dev/null 2>&1 || die "模板 $TEMPLATE_ID 不存在，请先运行 make-ubuntu2404-template.sh"
# 防止从"空壳模板"克隆出没有磁盘的 VM（会卡在 UEFI Shell）
if [ "$(qm config "$TEMPLATE_ID" | grep -c '^scsi0:')" -eq 0 ]; then
    die "模板 $TEMPLATE_ID 没有 scsi0（空壳），请先重做模板"
fi
if qm status "$VMID" >/dev/null 2>&1; then
    die "VMID $VMID 已存在"
fi
[ -f "$SSHKEY_FILE" ] || die "缺少 SSH 公钥：$SSHKEY_FILE"
pvesm status --storage "$STORAGE" >/dev/null 2>&1 || die "存储 $STORAGE 不存在"
ip link show "$BRIDGE" >/dev/null 2>&1 || die "网桥 $BRIDGE 不存在，请先按手册 5.4 创建 vmbr1"

IP="${NETPREFIX}.${VMID}"

if ping -c1 -W1 "$IP" >/dev/null 2>&1; then
    die "私网 IP $IP 已被占用（可能已有 VM 使用该地址）"
fi

echo ">>> 克隆模板 $TEMPLATE_ID -> $VMID  (${IP})"
qm clone "$TEMPLATE_ID" "$VMID" --name "lab-${VMID}" --full --storage "$STORAGE"

echo ">>> 资源配置：${CORES}C / ${MEM}MB / ${DISK}G"
qm set "$VMID" --sockets 1 --cores "$CORES" --memory "$MEM" --balloon 0

echo ">>> cloud-init 网络（仅 IPv4）"
qm set "$VMID" --ipconfig0 "ip=${IP}/${CIDR},gw=${GATEWAY}"
qm set "$VMID" --nameserver "$DNS1"
qm set "$VMID" --ciuser "$CIUSER" --sshkeys "$SSHKEY_FILE"

echo ">>> 磁盘扩容到 ${DISK}G"
qm resize "$VMID" scsi0 "${DISK}G"

if [ "$START" = "1" ]; then
    echo ">>> 启动 $VMID"
    qm start "$VMID"
    echo
    echo "完成。首次开机 cloud-init 约需 40-90 秒，之后可用："
    echo "    ssh ${CIUSER}@${IP}"
    echo "    qm guest cmd ${VMID} network-get-interfaces"
    echo
    echo "需要公网访问时：在宿主机 /etc/eip.map 里加一行 ${VMID}，再 systemctl restart eip"
else
    echo "完成（未启动）。手动启动：qm start ${VMID}"
fi
