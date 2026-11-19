#!/usr/bin/env bash
# ============================================================
# 实验集群节点初始化（P0/P1 通用）
# 用法：sudo bash p0-node-init.sh <hostname>
#   例：sudo bash p0-node-init.sh mysql-01
# 幂等：可重复执行
# ============================================================
set -euo pipefail

HOST="${1:?用法: sudo bash p0-node-init.sh <hostname>}"
DNS_IP="10.0.0.100"

[ "$(id -u)" -eq 0 ] || { echo "请用 sudo 执行" >&2; exit 1; }

# 等 cloud-init 跑完，避免 apt 锁冲突
if command -v cloud-init >/dev/null 2>&1; then
    cloud-init status --wait >/dev/null 2>&1 || true
fi

# ---------- 1. 主机名 ----------
hostnamectl set-hostname "$HOST"

# ---------- 2. hosts（37 台全量，先写全，未建的机器不影响） ----------
sed -i '/# lab-hosts-begin/,/# lab-hosts-end/d' /etc/hosts
cat >> /etc/hosts <<'EOF'
# lab-hosts-begin
10.0.0.100 bastion.lab.local bastion
10.0.0.101 ansible-02.lab.local ansible-02
10.0.0.102 ansible-03.lab.local ansible-03
10.0.0.103 jumpserver.lab.local jumpserver
10.0.0.110 lvs-01.lab.local lvs-01
10.0.0.111 lvs-02.lab.local lvs-02
10.0.0.120 nginx-01.lab.local nginx-01
10.0.0.121 nginx-02.lab.local nginx-02
10.0.0.130 app-blue-01.lab.local app-blue-01
10.0.0.131 app-blue-02.lab.local app-blue-02
10.0.0.132 app-green-01.lab.local app-green-01
10.0.0.133 app-green-02.lab.local app-green-02
10.0.0.150 mysql-01.lab.local mysql-01
10.0.0.151 mysql-02.lab.local mysql-02
10.0.0.152 mysql-03.lab.local mysql-03
10.0.0.160 redis-01.lab.local redis-01
10.0.0.161 redis-02.lab.local redis-02
10.0.0.162 redis-03.lab.local redis-03
10.0.0.170 minio-01.lab.local minio-01
10.0.0.171 minio-02.lab.local minio-02
10.0.0.172 minio-03.lab.local minio-03
10.0.0.180 es-01.lab.local es-01
10.0.0.181 es-02.lab.local es-02
10.0.0.182 es-03.lab.local es-03
10.0.0.190 prom-01.lab.local prom-01
10.0.0.191 grafana-01.lab.local grafana-01
10.0.0.200 gitlab-01.lab.local gitlab-01
10.0.0.201 jenkins-01.lab.local jenkins-01
10.0.0.202 jenkins-agent-01.lab.local jenkins-agent-01
10.0.0.203 jenkins-agent-02.lab.local jenkins-agent-02
10.0.0.210 harbor-01.lab.local harbor-01
10.0.0.211 harbor-02.lab.local harbor-02
10.0.0.220 k8s-m01.lab.local k8s-m01
10.0.0.221 k8s-m02.lab.local k8s-m02
10.0.0.222 k8s-m03.lab.local k8s-m03
10.0.0.230 k8s-w01.lab.local k8s-w01
10.0.0.231 k8s-w02.lab.local k8s-w02
# lab-hosts-end
EOF

# ---------- 3. 时区 + 关闭 IPv6 ----------
timedatectl set-timezone Asia/Shanghai
cat > /etc/sysctl.d/99-lab.conf <<'EOF'
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF
sysctl --system >/dev/null

# ---------- 4. 基础软件（此时仍用公网 DNS） ----------
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  curl vim htop net-tools dnsutils chrony jq rsync lsof sysstat tree \
  >/dev/null
systemctl enable --now chrony >/dev/null 2>&1 || true

# ---------- 5. DNS 指向 bastion（仅当 dnsmasq 已就绪） ----------
if dig +short +time=1 +tries=1 bastion.lab.local @"$DNS_IP" >/dev/null 2>&1; then
  if [ -f /etc/netplan/50-cloud-init.yaml ]; then
    sed -i "s/223\.5\.5\.5/$DNS_IP/" /etc/netplan/50-cloud-init.yaml
    netplan apply >/dev/null 2>&1 || true
  fi
  mkdir -p /etc/systemd/resolved.conf.d
  cat > /etc/systemd/resolved.conf.d/99-lab.conf <<EOF
[Resolve]
DNS=$DNS_IP 223.5.5.5
FallbackDNS=223.5.5.5
Domains=lab.local
EOF
  systemctl restart systemd-resolved >/dev/null 2>&1 || true
  echo "[dns] 已指向 $DNS_IP"
else
  echo "[dns] 跳过：$DNS_IP 的 dnsmasq 还没起来，暂用公网 DNS + /etc/hosts"
fi

echo
echo "初始化完成：$(hostname)  $(hostname -I | awk '{print $1}')"
echo "验证：getent hosts $(hostname).lab.local && timedatectl | head -3"
