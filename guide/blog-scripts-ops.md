---
category: 职业
difficulty: 中级
---

# 巡检 / 自愈 / 批量操作脚本集

::: tip 本篇定位
4 个真正在生产里用过的脚本：批量主机巡检、阈值巡检、服务自愈拉起、带白名单与二次确认的批量执行。每个都给「场景 → 完整带注释代码 → 用法 → 边界与风险」。
所有 Shell 已通过 `bash -n`、Python 已通过 `python3 -m py_compile` 自检。
:::

## 脚本一：批量主机巡检（CPU/内存/磁盘/端口）

**场景**：新接一批机器，或日常巡检，要一次性看每台机器的负载、内存、磁盘、关键端口是否在听，而不是一台台 ssh 上去敲。

```bash
#!/usr/bin/env bash
# batch_inspect.sh — 批量主机巡检（CPU/内存/磁盘/关键端口）
# 依赖：本机可通过 ssh 免密登录到目标主机；主机清单每行一个： user@host[:port]
set -u

HOSTS_FILE="${1:-hosts.txt}"          # 主机清单文件
SSH_USER="${SSH_USER:-ops}"            # 默认登录用户
SSH_OPTS="-o ConnectTimeout=5 -o StrictHostKeyChecking=no"

if [[ ! -f "$HOSTS_FILE" ]]; then
  echo "用法: $0 <hosts.txt>" >&2
  exit 1
fi

# 在远端执行的巡检命令：CPU/负载、内存、磁盘、关键端口
REMOTE_CMD='
echo "== 负载 =="; uptime
echo "== 内存 =="; free -h | awk "/Mem:/{print \$3\"/\"\$2\" used\"}"
echo "== 磁盘 =="; df -h --output=target,pcent | grep -vE "tmpfs|overlay"
echo "== 关键端口 =="; for p in 80 443 22 3306 6379; do
  ss -lnt 2>/dev/null | awk "{print \$4}" | grep -qE "[:.]$p\$" && echo "port $p LISTEN" || echo "port $p --";
done
'

while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  host="$line"
  port_arg=""
  if [[ "$host" == *:* ]]; then          # 支持 user@host:2222
    port_arg="-p ${host##*:}"
    host="${host%:*}"
  fi
  echo "################ $host ################"
  # shellcheck disable=SC2086
  ssh $SSH_OPTS $port_arg "${SSH_USER}@${host}" "$REMOTE_CMD" || echo "[!] $host ssh 失败"
done < "$HOSTS_FILE"
```

**用法**：

```bash
# hosts.txt 每行一台，可写 10.0.0.11 或 10.0.0.11:2222
chmod +x batch_inspect.sh
./batch_inspect.sh hosts.txt
```

**边界与风险**：

- 依赖 ssh 免密（密钥）；首次务必先用 `ssh ops@host` 手动验证能通，别脚本批量卡密码提示。
- `StrictHostKeyChecking=no` 方便但放弃了主机指纹校验，生产建议改用 `known_hosts` 预登记。
- 机器数量大时串行 ssh 会慢，可加 `&` + `wait` 并发，但别一次并发几百把自己 sshd 打爆。

## 脚本二：阈值巡检（磁盘/inode/句柄/连接数）

**场景**：要把巡检接进 cron，超阈值就以非 0 退出、触发告警。纯 Python、无第三方依赖，直接读 `/proc` 和 `df`。

```python
#!/usr/bin/env python3
"""threshold_inspect.py — 本机阈值巡检：磁盘使用率、inode、句柄、TCP 连接数。

无第三方依赖，直接读 /proc 与 df。超阈值打印 WARNING 并以非 0 退出（便于接告警/cron）。
"""
import argparse
import os
import subprocess
import sys


def disk_usage(threshold: int):
    """检查各挂载点磁盘块使用率，返回超阈值的点列表。"""
    bad = []
    # 用 df 拿到所有挂载点（含独立分区），更贴近运维实际
    out = subprocess.run(["df", "--output=target,pcent"], capture_output=True, text=True)
    for line in out.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        mount, pcent = line.rsplit(" ", 1)
        if mount in ("tmpfs", "overlay", "devtmpfs"):
            continue
        used = int(pcent.rstrip("%"))
        if used >= threshold:
            bad.append((mount, used))
    return bad


def inode_usage(threshold: int):
    """df -i 检查 inode 使用率。"""
    bad = []
    out = subprocess.run(["df", "-i", "--output=target,itotal,ipcent"],
                          capture_output=True, text=True)
    for line in out.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        mount, total, pcent = parts[0], parts[1], parts[2]
        if int(total) == 0:
            continue
        used = int(pcent.rstrip("%"))
        if used >= threshold:
            bad.append((mount, used))
    return bad


def fd_count(pid: str) -> int:
    """某进程打开的句柄数。"""
    try:
        return len(os.list(f"/proc/{pid}/fd"))
    except (FileNotFoundError, PermissionError):
        return -1


def tcp_established() -> int:
    """统计 TCP ESTABLISHED 连接数。"""
    count = 0
    for proto in ("tcp", "tcp6"):
        try:
            with open(f"/proc/net/{proto}") as f:
                for i, line in enumerate(f):
                    if i == 0:
                        continue
                    if line.split()[3] == "01":  # 01 = ESTABLISHED
                        count += 1
        except FileNotFoundError:
            pass
    return count


def main():
    ap = argparse.ArgumentParser(description="本机阈值巡检")
    ap.add_argument("--disk", type=int, default=85, help="磁盘使用率阈值%%")
    ap.add_argument("--inode", type=int, default=85, help="inode 使用率阈值%%")
    ap.add_argument("--conn", type=int, default=20000, help="TCP ESTABLISHED 连接数阈值")
    args = ap.parse_args()

    problems = 0

    for mount, used in disk_usage(args.disk):
        print(f"[WARNING] 磁盘 {mount} 使用率 {used}% >= {args.disk}%")
        problems += 1

    for mount, used in inode_usage(args.inode):
        print(f"[WARNING] inode {mount} 使用率 {used}% >= {args.inode}%")
        problems += 1

    conn = tcp_established()
    if conn >= args.conn:
        print(f"[WARNING] TCP ESTABLISHED = {conn} >= {args.conn}")
        problems += 1
    else:
        print(f"[OK] TCP ESTABLISHED = {conn}")

    # 举例：检查指定业务进程句柄数
    pid_file = "/run/order-svc.pid"
    if os.path.exists(pid_file):
        pid = open(pid_file).read().strip()
        fds = fd_count(pid)
        print(f"[INFO] 业务进程 {pid} 句柄数 = {fds}")
        if fds > 1000:
            print(f"[WARNING] 进程 {pid} 句柄数 {fds} > 1000，疑似 fd 泄漏")
            problems += 1

    if problems:
        print(f"[RESULT] {problems} 项超阈值")
        sys.exit(1)
    print("[RESULT] 全部正常")


if __name__ == "__main__":
    main()
```

**用法**：

```bash
python3 threshold_inspect.py                 # 默认阈值 85% / 20000 连接
python3 threshold_inspect.py --disk 90 --conn 50000   # 自定义阈值
# 接 cron：超阈值退出码为 1，可对接监控/告警
```

**边界与风险**：

- `--conn` 阈值要按机器规格定，大机器几万连接正常，别设太低导致误报。
- 句柄巡检依赖业务把 pid 写到 `/run/order-svc.pid`；没有 pid 文件就跳过，不会报错。
- 真正的监控建议用 Prometheus node_exporter，这个脚本适合没有监控系统的小机器做兜底。

## 脚本三：告警自愈（服务异常自动拉起并通知）

**场景**：关键小服务偶尔自己挂掉，等用户报障才发现太晚。用 cron 每分钟探一次，挂了自动 `systemctl restart`，并把结果推到机器人。

```bash
#!/usr/bin/env bash
# self_heal.sh — 告警自愈：检测 systemd 服务异常，自动拉起并通知。
# 用法: ./self_heal.sh <service-name>
# 由 cron 每 1 分钟执行；仅在服务"退出/未运行"时重启，避免反复抖动。
set -u

SVC="${1:-}"
WEBHOOK="${WEBHOOK:-}"          # 通知机器人地址，留空则只写日志
LOG="/var/log/self_heal.log"

[[ -z "$SVC" ]] && { echo "用法: $0 <service-name>" >&2; exit 1; }

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# 判断服务是否 active
if systemctl is-active --quiet "$SVC"; then
  exit 0                        # 正常，不打扰
fi

# 不在线 -> 记录并尝试拉起
echo "$(ts) [ALERT] $SVC 未运行，尝试重启" >> "$LOG"
systemctl restart "$SVC"
sleep 3

if systemctl is-active --quiet "$SVC"; then
  msg="✅ 自愈成功: $SVC 已自动拉起"
else
  msg="❌ 自愈失败: $SVC 重启后仍异常，请人工介入"
fi
echo "$(ts) $msg" >> "$LOG"

# 通知（curl 失败不影响主流程）
if [[ -n "$WEBHOOK" ]]; then
  curl -s -m 5 -X POST "$WEBHOOK" \
       -H 'Content-Type: application/json' \
       -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"[$(hostname)] $msg\"}}" || true
fi
```

**用法**：

```bash
# crontab -e 加一行，每分钟探一次
* * * * * WEBHOOK=https://oapi.dingtalk.com/robot/send?key=xxx /opt/self_heal.sh order-svc
```

**边界与风险**：

::: danger 自愈不是万能药
- 服务如果是"启动即崩"（配置错误/依赖挂了），自愈会每分钟重启一次，白白刷日志。**务必加"重启失败则不再自动重启、转人工"的逻辑**（本脚本已在重启失败时发告警，但不会退避）。
- 对有状态服务（数据库、MQ）不要盲目自动重启，先告警人工判断。
- webhook 地址是敏感信息，别硬编码进脚本提交到 Git，用环境变量或配置文件注入。
:::

## 脚本四：批量执行 / 分发（白名单 + 二次确认）

**场景**：要在多台机器上执行同一条命令（reload Nginx、清理缓存）。最怕一条命令扫到不该动的机器。这个脚本内置白名单过滤 + 演练模式 + 二次确认。

```bash
#!/usr/bin/env bash
# batch_exec.sh — 带白名单与二次确认的批量执行。
# 用法:
#   ./batch_exec.sh hosts.txt "systemctl reload nginx"
#   DRY_RUN=1 ./batch_exec.sh hosts.txt "rm -rf /tmp/old"   # 只演练不执行
# 安全设计：目标主机必须命中白名单；执行前打印计划并要求输入 yes。
set -u

HOSTS_FILE="${1:-}"
CMD="${2:-}"
# 白名单：只有命中这些网段/主机才允许操作（按需改成自己的）
ALLOW_REGEX='^ops-[0-9]+\.internal$|^10\.0\.(11|21)\.'

[[ -z "$HOSTS_FILE" || -z "$CMD" ]] && {
  echo "用法: $0 <hosts.txt> \"<要执行的命令>\"" >&2; exit 1; }
[[ -f "$HOSTS_FILE" ]] || { echo "找不到 $HOSTS_FILE" >&2; exit 1; }

# 1) 收集并过滤命中白名单的主机
targets=()
while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  host="${line%%:*}"                 # 去掉可能的 :port
  if [[ "$host" =~ $ALLOW_REGEX ]]; then
    targets+=("$line")
  else
    echo "[BLOCK] $host 不在白名单，跳过" >&2
  fi
done < "$HOSTS_FILE"

[[ ${#targets[@]} -eq 0 ]] && { echo "没有可执行的目标主机" >&2; exit 1; }

echo "即将在 ${#targets[@]} 台主机上执行:"
echo "  命令: $CMD"
printf '  目标: %s\n' "${targets[@]}"

# 2) 二次确认（非交互环境可用 FORCE=1 跳过，但建议保留）
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "[DRY_RUN] 仅演练，不实际执行"
  exit 0
fi
if [[ "${FORCE:-0}" != "1" ]]; then
  read -r -p "确认执行？输入 yes 继续: " ans
  [[ "$ans" == "yes" ]] || { echo "已取消"; exit 1; }
fi

# 3) 逐台执行，单台失败不影响其他
for t in "${targets[@]}"; do
  port_arg=""
  host="$t"
  if [[ "$t" == *:* ]]; then port_arg="-p ${t##*:}"; host="${t%:*}"; fi
  echo "==> $host"
  # shellcheck disable=SC2086
  ssh -o ConnectTimeout=5 $port_arg "ops@${host}" "$CMD" \
    && echo "   [ok]" || echo "   [fail]"
done
```

**用法**：

```bash
# 先演练：只打印会在哪些机器执行什么，不动手
DRY_RUN=1 ./batch_exec.sh hosts.txt "systemctl reload nginx"

# 确认无误后正式执行（会要求输入 yes）
./batch_exec.sh hosts.txt "systemctl reload nginx"
```

**边界与风险**：

- `ALLOW_REGEX` 必须改成自己环境的网段/命名，否则一台都匹配不上（或误匹配）。
- 危险命令（`rm`、`drop`、`reboot`）建议强制先 `DRY_RUN`，并在变更窗口双人复核。
- 远端命令是字符串拼接执行，别把用户输入直接塞进来，避免注入。

## 相关速查

- 备份/清理/证书巡检的另一组脚本：[备份 / 清理 / 证书巡检脚本集](./blog-scripts-backup)
- 这些脚本背后的现场法则：[现场经验法则与"土办法"](./blog-field-rules)
- 上线/巡检/应急清单：[运维 Checklist 大全](/reference/ops-checklists)
- 主机性能命令随查：[Linux 命令速查](/reference/linux-commands)
- 用 Ansible 做更工程化的批量管理：[Ansible](./automation-ansible)
