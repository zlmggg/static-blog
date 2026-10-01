---
category: 职业
difficulty: 中级
---

# 备份 / 清理 / 证书巡检脚本集

::: tip 本篇定位
4 个数据保全类脚本：日志切割清理、带校验和与轮转的备份、证书到期巡检、数据一致性校验。每个给「场景 → 完整带注释代码 → 用法 → 边界与风险」。
所有 Shell 已通过 `bash -n`、Python 已通过 `python3 -m py_compile`，备份与数据校验脚本已做本地功能验证。
:::

## 脚本一：日志按大小 / 天数切割清理

**场景**：应用日志持续增长，单文件超过 100MB 就轮转，备份日志保留 14 天自动删旧。

```bash
#!/usr/bin/env bash
# log_clean.sh — 日志按大小与天数切割清理。
# 场景：某个目录下的应用日志持续增长，超过大小就轮转，超过天数就删旧文件。
set -u

LOG_DIR="${1:-/var/log/myapp}"
MAX_SIZE_MB="${MAX_SIZE_MB:-100}"      # 单文件超过此大小则轮转
KEEP_DAYS="${KEEP_DAYS:-14}"          # 保留天数

[[ -d "$LOG_DIR" ]] || { echo "目录不存在: $LOG_DIR" >&2; exit 1; }

ts() { date '+%Y%m%d-%H%M%S'; }

# 1) 按大小轮转：超过 MAX_SIZE_MB 的日志，截断成 .1 备份
for f in "$LOG_DIR"/*.log; do
  [[ -f "$f" ]] || continue
  size_kb=$(du -k "$f" | awk '{print $1}')
  max_kb=$(( MAX_SIZE_MB * 1024 ))
  if (( size_kb >= max_kb )); then
    # 截断而非 rm：正在写的进程句柄不丢，空间立即释放
    cp "$f" "${f}.$(ts).bak"
    : > "$f"
    echo "轮转: $f -> ${f}.$(ts).bak"
  fi
done

# 2) 按天数清理：删除 mtime 超过 KEEP_DAYS 的 .bak 日志
find "$LOG_DIR" -name "*.bak" -type f -mtime "+${KEEP_DAYS}" -print -delete
```

**用法**：

```bash
chmod +x log_clean.sh
./log_clean.sh /var/log/myapp
# 接 cron：每天凌晨跑一次
# 0 3 * * * /opt/log_clean.sh /var/log/myapp
```

**边界与风险**：

- 生产更推荐系统自带的 `logrotate`（支持压缩、postrotate reload），这个脚本适合没有 logrotate 或自定义需求的场景。
- `: > "$f"` 截断能立即释放空间且不影响正在写的进程；**别用 `rm`**，否则句柄不释放、空间不回收（见[踩坑实录](./blog-war-stories)第 4 条）。

## 脚本二：自动备份 + 完整性校验 + 轮转 + 失败告警

**场景**：每天备份业务目录，打包后生成校验和、立即回读验证、只留最近 7 份，失败就推告警。

```bash
#!/usr/bin/env bash
# backup.sh — 自动备份 + 完整性校验 + 保留轮转 + 失败告警。
# 场景：把某个目录打包备份，生成校验和，只保留最近 N 份，失败则推告警。
set -u

SRC="${SRC:-/data/myapp}"                 # 要备份的目录
DST="${DST:-/backup/myapp}"               # 备份存放目录
KEEP="${KEEP:-7}"                        # 保留最近份数
WEBHOOK="${WEBHOOK:-}"                    # 失败告警地址（可空）

[[ -d "$SRC" ]] || { echo "源目录不存在: $SRC" >&2; exit 1; }
mkdir -p "$DST"

ts() { date '+%Y%m%d-%H%M%S'; }
stamp="$(ts)"
ARCHIVE="$DST/backup-$stamp.tar.gz"

fail() {
  echo "[FAIL] $1" >&2
  [[ -n "$WEBHOOK" ]] && curl -s -m 5 -X POST "$WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"[备份失败][$(hostname)] $1\"}}" || true
  exit 1
}

# 1) 打包
tar -czf "$ARCHIVE" -C "$(dirname "$SRC")" "$(basename "$SRC")" || fail "tar 打包失败: $ARCHIVE"

# 2) 生成校验和
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256" || fail "生成校验和失败"

# 3) 立即回读校验（验证备份本身没坏）
if ! (cd "$DST" && sha256sum -c "$(basename "$ARCHIVE").sha256" >/dev/null 2>&1); then
  rm -f "$ARCHIVE" "$ARCHIVE.sha256"
  fail "备份校验失败，已删除坏包"
fi

# 4) 保留轮转：只留最近 KEEP 份（按文件名时间排序）
ls -1t "$DST"/backup-*.tar.gz 2>/dev/null | tail -n +$(( KEEP + 1 )) | while read -r old; do
  rm -f "$old" "$old.sha256"
done

echo "[OK] 备份完成: $ARCHIVE ($(du -h "$ARCHIVE" | awk '{print $1}'))"
```

**用法**：

```bash
SRC=/data/myapp DST=/backup/myapp KEEP=7 bash backup.sh
# 数据库备份：先 mysqldump 导出成 sql 文件，再走本脚本打包
```

**边界与风险**：

::: warning 备份三问
- **备份了不等于能恢复**：定期做一次"从备份恢复到测试机"的演练，否则备份只是心理安慰。
- **备份目录别和源目录在同一台机器同一块盘**，机器/磁盘坏了备份一起没；重要数据异地或异盘。
- `KEEP` 份数要结合备份大小算容量，别把备份盘写满反噬业务。
:::

## 脚本三：证书 / 域名到期天数巡检

**场景**：定期扫一批域名证书，剩余不足 30 天就告警，别让证书深夜过期（见[踩坑实录](./blog-war-stories)第 10 条）。

```python
#!/usr/bin/env python3
"""cert_expiry.py — 证书到期天数巡检。

用法:
    python3 cert_expiry.py example.com 443 example.org 443
    python3 cert_expiry.py --warn 30 example.com 443
超过 warn 天则打印 WARNING 并以非 0 退出（接告警/cron）。
依赖：系统 openssl 命令。
"""
import argparse
import subprocess
import sys
from datetime import datetime, timezone


def cert_expiry_days(host: str, port: int) -> int:
    """通过 openssl 拿到证书到期时间，返回距今天的天数。"""
    cmd = (
        f"echo | openssl s_client -connect {host}:{port} -servername {host} 2>/dev/null "
        f"| openssl x509 -noout -enddate"
    )
    out = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
    # 输出形如：notAfter=Jan  1 12:00:00 2027 GMT
    line = out.stdout.strip()
    if not line.startswith("notAfter="):
        raise RuntimeError(f"无法获取 {host}:{port} 证书: {out.stderr or line}")
    expires = line.split("=", 1)[1].strip()
    dt = datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    return (dt - datetime.now(timezone.utc)).days


def main():
    ap = argparse.ArgumentParser(description="证书到期巡检")
    ap.add_argument("--warn", type=int, default=30, help="提前多少天告警")
    ap.add_argument("targets", nargs="+", help="host port 成对给出，如 example.com 443")
    args = ap.parse_args()

    if len(args.targets) % 2 != 0:
        print("目标需按 host port 成对给出", file=sys.stderr)
        sys.exit(2)

    bad = 0
    pairs = list(zip(args.targets[0::2], args.targets[1::2]))
    for host, port in pairs:
        try:
            days = cert_expiry_days(host, int(port))
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] {host}:{port} {e}")
            bad += 1
            continue
        if days < args.warn:
            print(f"[WARNING] {host}:{port} 证书 {days} 天后到期 (< {args.warn})")
            bad += 1
        else:
            print(f"[OK] {host}:{port} 证书剩余 {days} 天")

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
```

**用法**：

```bash
python3 cert_expiry.py --warn 30 example.com 443 api.example.com 443
# 接 cron：每周一跑，超阈值退出码 1 接告警
```

**边界与风险**：

- 依赖能出网访问目标 443（内网证书要在能访问内网的机器上跑）。
- 域名/证书的统一台账见[密钥与证书管理](./devops-secrets)。

## 脚本四：数据一致性校验（校验和 / 行数比对）

**场景**：主从切换后、或备份恢复后，要确认两份目录数据是否一致。脚本逐文件算 sha256，文本文件额外比对行数。

```python
#!/usr/bin/env python3
"""data_check.py — 数据一致性校验。

场景：主从切换后 / 备份恢复后，要确认两份数据一致。
本脚本对比两个目录下同名文件的 sha256，并对纯文本数据文件做行数比对。
退出码：0 = 一致；1 = 发现不一致；2 = 用法/环境错误。
"""
import argparse
import hashlib
import os
import sys


def sha256_of(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            buf = f.read(chunk)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def line_count(path: str) -> int:
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def main():
    ap = argparse.ArgumentParser(description="目录数据一致性校验")
    ap.add_argument("dir_a", help="基准目录（如新主）")
    ap.add_argument("dir_b", help="对比目录（如旧主/备份）")
    args = ap.parse_args()

    if not (os.path.isdir(args.dir_a) and os.path.isdir(args.dir_b)):
        print("两个参数都必须是目录", file=sys.stderr)
        sys.exit(2)

    files_a = {f for f in os.listdir(args.dir_a) if os.path.isfile(os.path.join(args.dir_a, f))}
    files_b = {f for f in os.listdir(args.dir_b) if os.path.isfile(os.path.join(args.dir_b, f))}

    problems = 0

    # 1) 文件清单差异
    only_a = files_a - files_b
    only_b = files_b - files_a
    for f in sorted(only_a):
        print(f"[DIFF] 仅在基准目录存在: {f}")
        problems += 1
    for f in sorted(only_b):
        print(f"[DIFF] 仅在对比目录存在: {f}")
        problems += 1

    # 2) 同名文件做校验和 + 行数比对
    for f in sorted(files_a & files_b):
        pa, pb = os.path.join(args.dir_a, f), os.path.join(args.dir_b, f)
        if sha256_of(pa) != sha256_of(pb):
            print(f"[DIFF] 内容不一致: {f}")
            problems += 1
            continue
        # 文本文件额外比对行数，快速定位差异规模
        if f.endswith((".txt", ".csv", ".sql", ".log")):
            la, lb = line_count(pa), line_count(pb)
            if la != lb:
                print(f"[DIFF] {f} 行数不同: 基准 {la} vs 对比 {lb}")
                problems += 1
            else:
                print(f"[OK] {f} 校验和一致（{la} 行）")
        else:
            print(f"[OK] {f} 校验和一致")

    if problems:
        print(f"[RESULT] {problems} 处不一致")
        sys.exit(1)
    print("[RESULT] 两份数据一致")


if __name__ == "__main__":
    main()
```

**用法**：

```bash
python3 data_check.py /data/new-master /data/old-master
# 一致退出 0，不一致退出 1，可接告警/变更流程
```

**边界与风险**：

- 大文件全量算 sha256 会读全量磁盘，大数据量（几十 GB）建议在业务低峰跑，或只校验关键表/文件。
- 数据库层面的一致性更推荐 `mysqldump | md5sum` 按表比对，或用主库 `CHECKSUM TABLE`；本脚本适合文件型数据。

## 相关速查

- 巡检/自愈/批量操作的另一组脚本：[巡检 / 自愈 / 批量操作脚本集](./blog-scripts-ops)
- 为什么要做备份与灾备：[容量规划、高可用与灾备](./sre-capacity-dr)
- 密钥与证书的统一管理：[密钥与证书管理](./devops-secrets)
- 备份/割接/灾备清单：[运维 Checklist 大全](/reference/ops-checklists)

### 官方文档

- GNU tar 备份：https://www.gnu.org/software/tar/manual/html_node/tar-tutorial.html
- sha256sum 校验：https://man7.org/linux/man-pages/man1/sha256sum.1.html
- OpenSSL s_client 检查证书：https://www.openssl.org/docs/manmaster/man1/openssl-s_client.html
- logrotate：https://man7.org/linux/man-pages/man8/logrotate.8.html
