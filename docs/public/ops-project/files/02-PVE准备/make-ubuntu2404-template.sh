#!/usr/bin/env bash
# ============================================================
# 在 PVE 宿主机上以 root 执行，制作 Ubuntu 24.04 cloud-init 模板
#   bash make-ubuntu2404-template.sh
# 可选环境变量：
#   TPL_ID=9000 TPL_NAME=ubuntu-2404-ci STORAGE=nvme-lvm BRIDGE=vmbr1 DISK_GB=10
#
# 设计要点：
#   1. 不解析 qm importdisk 的屏幕输出，卷名从 qm config 里读
#   2. 每一步都校验，失败立刻退出，绝不留下"空壳模板"
#   3. 转模板前强制检查 scsi0 / efidisk0 / ide2 / cicustom
# ============================================================
set -euo pipefail

TPL_ID="${TPL_ID:-9000}"
TPL_NAME="${TPL_NAME:-ubuntu-2404-ci}"
STORAGE="${STORAGE:-nvme-lvm}"          # NVMe thin 池（见 PVE 手册 6.1）
BRIDGE="${BRIDGE:-vmbr1}"
DISK_GB="${DISK_GB:-10}"

IMG_DIR="/var/lib/vz/template/iso"
IMG="${IMG_DIR}/noble-server-cloudimg-amd64.img"
# 国内优先用清华镜像，失败再回官方源
IMG_URL="https://mirrors.tuna.tsinghua.edu.cn/ubuntu-cloud-images/noble/current/noble-server-cloudimg-amd64.img"
IMG_URL_FALLBACK="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
SNIPPET_REL="snippets/ubuntu-2404-vendor.yaml"
SNIPPET_ABS="/var/lib/vz/${SNIPPET_REL}"

die() { echo "[ERROR] $*" >&2; exit 1; }
step() { echo; echo ">>> $*"; }

# ---------- 0. 环境检查 ----------
[ "$(id -u)" -eq 0 ] || die "请用 root 执行"
command -v qm >/dev/null 2>&1 || die "未找到 qm，请在本机 PVE 上运行"
pvesm status --storage "$STORAGE" >/dev/null 2>&1 || die "存储 $STORAGE 不存在"
ip link show "$BRIDGE" >/dev/null 2>&1 || die "网桥 $BRIDGE 不存在，请先建好 vmbr1"

mkdir -p "$IMG_DIR" /var/lib/vz/snippets
# 确保 local 存储启用 snippets（cloud-init 自定义配置必需）
pvesm set local --content iso,vztmpl,backup,snippets >/dev/null 2>&1 || true

# ---------- 1. 云镜像 ----------
step "1/8 准备云镜像"
if [ ! -s "$IMG" ]; then
    echo "    下载中（清华源）..."
    wget -O "$IMG" "$IMG_URL" || wget -O "$IMG" "$IMG_URL_FALLBACK" || die "镜像下载失败"
fi
[ -s "$IMG" ] || die "镜像文件为空：$IMG"
ls -lh "$IMG"

[ -f "$SNIPPET_ABS" ] || die "缺少 $SNIPPET_ABS（vendor 配置），请先上传"

# ---------- 2. 清理旧模板 ----------
if qm status "$TPL_ID" >/dev/null 2>&1; then
    step "清理已存在的 ID $TPL_ID"
    qm set "$TPL_ID" --protection 0 >/dev/null 2>&1 || true
    qm stop "$TPL_ID" >/dev/null 2>&1 || true
    qm destroy "$TPL_ID" --purge
fi

# ---------- 3. 建空 VM ----------
step "2/8 创建空 VM $TPL_ID"
qm create "$TPL_ID" \
    --name "$TPL_NAME" --ostype l26 \
    --machine q35 --bios ovmf --cpu host \
    --sockets 1 --cores 2 --memory 2048 --balloon 0 \
    --net0 "virtio,bridge=${BRIDGE}" \
    --scsihw virtio-scsi-single --agent enabled=1 \
    --serial0 socket --vga std --onboot 0

# ---------- 4. 导入并挂载磁盘 ----------
step "3/8 导入云镜像"
qm importdisk "$TPL_ID" "$IMG" "$STORAGE" || die "qm importdisk 失败"

step "4/8 挂载磁盘到 scsi0"
# 关键：从配置里读实际卷名，不解析 importdisk 的 stdout
VOL="$(qm config "$TPL_ID" | awk -F': ' '/^unused[0-9]+:/{print $2}' | tail -n1)"
if [ -z "$VOL" ]; then
    qm config "$TPL_ID"
    die "没找到导入后的卷（unusedN），请检查上面的配置"
fi
echo "    卷名：$VOL"

qm set "$TPL_ID" --scsi0 "${VOL},discard=on,ssd=1,iothread=1" || die "挂载 scsi0 失败"
qm set "$TPL_ID" --delete unused0 >/dev/null 2>&1 || true
# 用 grep -c 而不是 grep -q：-q 会提前退出，配合 pipefail 可能误判
if [ "$(qm config "$TPL_ID" | grep -c '^scsi0:')" -eq 0 ]; then
    die "scsi0 挂载后校验失败"
fi

# ---------- 5. EFI + cloud-init ----------
step "5/8 挂 EFI 盘与 cloud-init 盘"
qm set "$TPL_ID" --efidisk0 "${STORAGE}:1,efitype=4m,pre-enrolled-keys=0" || die "创建 efidisk0 失败"
qm set "$TPL_ID" --ide2 "${STORAGE}:cloudinit" || die "创建 cloud-init 盘失败"
qm set "$TPL_ID" --boot order=scsi0 || die "设置启动顺序失败"
qm set "$TPL_ID" --ciupgrade 0
qm set "$TPL_ID" --cicustom "vendor=local:${SNIPPET_REL}" || die "挂载 vendor-data 失败"

# ---------- 6. 扩容 ----------
step "6/8 基础盘扩容到 ${DISK_GB}G"
qm resize "$TPL_ID" scsi0 "${DISK_GB}G" || die "扩容失败"

# ---------- 7. 转模板前总校验 ----------
step "7/8 转模板前校验"
for k in scsi0 efidisk0 ide2 cicustom boot; do
    if [ "$(qm config "$TPL_ID" | grep -c "^${k}:")" -eq 0 ]; then
        qm config "$TPL_ID"
        die "缺少 ${k}，终止（否则会生成空壳模板）"
    fi
    echo "    OK: $k"
done

# ---------- 8. 转模板 ----------
step "8/8 转模板并加保护"
qm template "$TPL_ID"
qm set "$TPL_ID" --protection 1

echo
echo "================ 模板创建完成 ================"
qm config "$TPL_ID"
echo "=============================================="
echo "下一步：bash create-lab-vm.sh 110 2 2048 20"
