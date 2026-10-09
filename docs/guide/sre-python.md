---
category: 架构
difficulty: 中级
---

# Python 运维自动化

::: tip 本篇定位
Shell 写着写着就变成几百行难维护的胶水脚本，处理 JSON、并发、重试、异常时尤其痛苦。Python 是 SRE 的第二把刀：用它做批量 SSH、调 API、处理监控数据、定时巡检，比 Shell 工程化得多。这篇给一套**能直接抄去生产用**的 Python 运维工具箱与一个完整巡检告警小工具。
本篇版本：Python 3.14.7（当前稳定版，3.13.15 为上一维护版）、requests 2.34.2、paramiko 5.0.0。示例代码用 Python 3.10+ 语法，3.14/3.13 均可直接运行。所有版本以官网当前稳定版为准。
:::

## 一、环境与编码规范

### 1.1 小白类比：Python 运维脚本好在哪

Shell 像"用一把瑞士军刀砍树"——应急快，但树高了就够不着。Python 像"正规工具箱"：

- 处理 JSON / CSV、做字符串切分、调 HTTP API，Python 标准库自带，Shell 要拼 `jq`/`awk` 很痛。
- 并发跑 100 台机器，Python 用线程池几行搞定，Shell 要 `&` + `wait` 自己管。
- 出错能 `try/except` 精确处理，Shell 脚本一个报错就糊一脸不知道哪挂了。

但**简单一次性任务** Shell 仍然更快。什么时候用谁，见第六节对比。

### 1.2 环境准备

```bash
# 用官方稳定版（示例 3.14；3.13.15 也完全够用）
python3 --version            # 确认 >= 3.10

# 建虚拟环境，别污染系统 Python
python3 -m venv ~/ops-venv
source ~/ops-venv/bin/activate

# 装依赖（写死版本，requirements.txt）
pip install requests==2.34.2 paramiko==5.0.0
```

`requirements.txt`：

```text
requests==2.34.2
paramiko==5.0.0
```

编码规范简述：脚本顶部 `#!/usr/bin/env python3` + `# -*- coding: utf-8 -*-`；函数拆小、写 docstring；配置从文件/环境变量读，别硬编码 IP 和密码；日志打全，别 `print` 一把梭。

## 二、subprocess：安全调用外部命令

### 2.1 核心原则：用参数数组，不要 shell=True

```python
import subprocess

def run_cmd(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """安全地跑外部命令，返回 (returncode, stdout, stderr)。"""
    try:
        p = subprocess.run(
            cmd,                       # 用列表传参数，天然防 shell 注入
            capture_output=True,
            text=True,                 # 输出按字符串解码，不拿 bytes
            timeout=timeout,
            check=False,               # 不主动抛异常，自己判断 returncode
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", f"命令超时({timeout}s): {' '.join(cmd)}"

# 用法：每个参数一个列表元素，不要拼成字符串
rc, out, err = run_cmd(["df", "-h", "/"])
print(rc, out)
```

| 写法 | 风险 |
|---|---|
| `subprocess.run(["ls", "-l", path])` | ✅ 安全，参数列表 |
| `subprocess.run(f"ls -l {path}", shell=True)` | ❌ 危险：path 里有 `; rm -rf` 就中招 |
| 不传 `timeout` | ❌ 命令卡住会把脚本永远挂住 |

::: warning shell=True 几乎不要用
只有当命令本身依赖 shell 特性（管道、通配、重定向）时才考虑，并且绝不能把用户可控字符串拼进去。运维脚本默认走参数数组。
:::

## 三、paramiko：批量 SSH 执行与文件传输

### 3.1 封装一个 SSH 助手

```python
import paramiko
from dataclasses import dataclass

@dataclass
class SSHResult:
    host: str
    code: int
    stdout: str
    stderr: str

def ssh_exec(host: str, user: str, key_path: str, cmd: str,
             port: int = 22, timeout: int = 30) -> SSHResult:
    """用私钥登录远程主机执行一条命令。"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host, port=port, username=user,
            key_filename=key_path, timeout=timeout,
            allow_agent=False, look_for_keys=False,
        )
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        code = stdout.channel.recv_exit_status()
        return SSHResult(host, code,
                         stdout.read().decode().strip(),
                         stderr.read().decode().strip())
    finally:
        client.close()

def scp_upload(host: str, user: str, key_path: str,
               local_path: str, remote_path: str):
    """上传文件到远程主机（SFTP）。"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=user, key_filename=key_path)
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
    finally:
        client.close()
```

::: tip 并发跑多台
上面是串行的。机器一多，用 `concurrent.futures.ThreadPoolExecutor` 并发，每台一个线程，几十台几秒就跑完——这是 Python 比 Shell 舒服最多的地方（见第五节综合工具）。
:::

## 四、requests：调用 REST API

### 4.1 带超时与重试的 Session

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3, backoff_factor=1,          # 1s,2s,4s 退避
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s

# GET 示例：查 Prometheus 瞬时指标
sess = make_session()
resp = sess.get(
    "http://prometheus:9090/api/v1/query",
    params={"query": "node_filesystem_avail_bytes{mountpoint='/'}"},
    timeout=10,
)
resp.raise_for_status()          # 非 2xx 直接抛异常
data = resp.json()
print(data["data"]["result"])
```

### 4.2 调 K8s API（带分页）

```python
def list_pods(api_server: str, token: str, namespace: str = "default"):
    """分页拉取某命名空间的 Pod 列表。"""
    s = make_session()
    s.headers["Authorization"] = f"Bearer {token}"
    pods, _continue = [], None
    while True:
        params = {"limit": 100}
        if _continue:
            params["continue"] = _continue
        r = s.get(f"{api_server}/api/v1/namespaces/{namespace}/pods",
                  params=params, timeout=10, verify=False)
        r.raise_for_status()
        body = r.json()
        pods.extend(body["items"])
        _continue = body.metadata.get("continue")
        if not _continue:
            break
    return pods
```

> 实战中调 K8s API 更推荐官方 `kubernetes` 客户端库；这里用 requests 演示通用分页思路。

## 五、综合实战：批量巡检磁盘/内存并告警

下面这个小工具：并发 SSH 到一组机器，收集磁盘和内存使用率，超阈值的汇总后打印告警。可直接跑。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("inspect")

HOSTS = ["192.168.10.21", "192.168.10.22", "192.168.10.23"]
USER = "ops"
KEY = "/home/ops/.ssh/id_rsa"
DISK_THRESHOLD = 80     # 磁盘使用率告警阈值 %
MEM_THRESHOLD = 85      # 内存使用率告警阈值 %

@dataclass
class HostReport:
    host: str
    disk_pct: int = 0
    mem_pct: int = 0
    errors: list = field(default_factory=list)

def inspect_one(host: str) -> HostReport:
    rep = HostReport(host=host)
    try:
        # 磁盘根分区使用率
        _, out, _ = _ssh(host, "df --output=pcent / | tail -1 | tr -d ' %'")
        rep.disk_pct = int(out)
        # 内存使用率
        _, out, _ = _ssh(host, "free | awk '/Mem:/{printf \"%d\", $3/$2*100}'")
        rep.mem_pct = int(out)
    except Exception as e:                 # 单台失败不影响其它
        rep.errors.append(str(e))
    return rep

def _ssh(host, cmd):
    # 复用第三节的 ssh_exec
    return ssh_exec(host, USER, KEY, cmd)

def main():
    alerts = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(inspect_one, h): h for h in HOSTS}
        for fut in as_completed(futures):
            rep = fut.result()
            log.info("%s 磁盘=%s%% 内存=%s%%", rep.host, rep.disk_pct, rep.mem_pct)
            if rep.errors:
                alerts.append(f"[ERROR] {rep.host} 采集失败: {rep.errors}")
                continue
            if rep.disk_pct >= DISK_THRESHOLD:
                alerts.append(f"[DISK] {rep.host} 根分区已用 {rep.disk_pct}% >= {DISK_THRESHOLD}%")
            if rep.mem_pct >= MEM_THRESHOLD:
                alerts.append(f"[MEM] {rep.host} 内存已用 {rep.mem_pct}% >= {MEM_THRESHOLD}%")

    print("\n===== 巡检结果 =====")
    if alerts:
        print("发现异常：")
        for a in alerts:
            print(" -", a)
        # 这里可接 webhook（企业微信/钉钉/Prometheus Alertmanager）发告警
    else:
        print("全部正常")

if __name__ == "__main__":
    main()
```

## 六、数据处理、定时任务与打包

### 6.1 json / csv / pandas

```python
import json, csv

# json：最常用，API 返回基本都是它
obj = json.loads('{"name": "web", "replicas": 3}')
text = json.dumps(obj, ensure_ascii=False, indent=2)

# csv：读巡检报表
with open("report.csv", newline="") as f:
    for row in csv.DictReader(f):
        print(row["host"], row["disk_pct"])
```

数据量大、要做分组统计/画图时再上 `pandas`；十几行以内的小表，标准库 csv 就够，别为这点事引重依赖。

### 6.2 APScheduler vs 系统 cron

| 对比 | 系统 cron | APScheduler |
|---|---|---|
| 配置 | crontab 文件 | Python 代码里定义 |
| 依赖脚本环境 | 要自己配 PATH/虚拟环境 | 直接在进程内跑 |
| 并发/错过策略 | 基本不管 | 支持 misfire、并发控制、持久化 job |
| 监控 | 难 | 可接日志/告警 |
| 适合 | 简单、低频、单台 | 复杂调度、需要重试与状态 |

```python
# APScheduler 示例：每天 09:00 跑一次巡检
from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()
sched.add_job(main, "cron", hour=9, minute=0)
sched.start()
```

### 6.3 日志与异常

- 用 `logging` 模块，别 `print`；生产打到文件并按天切割。
- 外部调用（SSH/HTTP）一律 try/except + 超时 + 重试，单台失败不要拖垮整个批量任务（综合工具里已示范）。
- 脚本打包：小工具直接 `scp` 到 `/usr/local/bin/`；要分发给别人用 `pyinstaller` 打成单二进制，或写 Docker 镜像。

## 七、Python vs Shell 选型

| 场景 | 选谁 |
|---|---|
| 一行命令、临时过滤日志 | Shell / 管道 |
| 批量 SSH 几十台上百台 | Python（paramiko + 线程池） |
| 调 REST API、处理 JSON | Python（requests） |
| 定时巡检 + 告警 | Python（APScheduler） |
| 简单定时跑个备份脚本 | Shell + cron |
| 需要错误处理、并发、可维护 | Python |

> 边界很模糊时：先 Shell 快速跑通，一旦开始写 `if/for/管道套管道` 超过 30 行，就该迁到 Python。Ansible（见 [Ansible 自动化](./automation-ansible)）本质也是 Python 封装的批量 SSH 框架。

## 八、常见问题排错

| 现象 | 原因 | 解决 |
|---|---|---|
| `paramiko` 连接被拒/卡住 | 用户名/密钥错、网络不通、没设 timeout | 先手动 `ssh -i key user@host` 验证；代码里必传 timeout |
| subprocess 结果是 bytes 不是 str | 没加 `text=True` | 加 `text=True` 或 `.decode()` |
| requests 偶发偶发超时不重试 | 没配 Retry / 没设 timeout | 用上面的 make_session，所有请求带 timeout |
| SSH 批量跑很慢 | 串行执行 | 换 `ThreadPoolExecutor` 并发 |
| 脚本在 cron 里跑不起来 | PATH/虚拟环境没加载 | cron 里写绝对路径，或 `source venv/bin/activate` 后再跑 |
| 中文输出乱码 | 编码不是 UTF-8 | 头文件声明 utf-8；读文件显式 `encoding="utf-8"` |
| 解析 df/free 输出字段变了 | 依赖文本格式太脆 | 用 `--output=` 固定列、`awk` 按列取；跨发行版先测 |

::: warning 生产红线
- 密码/私钥不要硬编码进脚本，用环境变量或密钥管理；私钥文件权限 600。
- 批量操作脚本先在一台测试机/用 `--dry-run` 跑通，再放开全量；删除类操作加二次确认。
- 所有外部调用（SSH/HTTP/subprocess）必须有超时，避免一台机器挂住拖垮整批。
- 脚本权限最小化，巡检账号只读；告警 webhook 地址走配置文件，别提交真实 token。
- 依赖版本写死进 requirements.txt，生产部署可复现，别 `pip install -U` 一把梭。
:::

## 相关速查

- Shell 基础：[Linux Shell](./linux-shell)、[Linux 命令速查](/reference/linux-commands)
- 批量自动化：[Ansible 自动化](./automation-ansible)
- 监控与 API：[Prometheus 监控](./monitor-prometheus-01-intro)、[OpenTelemetry](./monitor-opentelemetry)
- 容器与 K8s：[Helm 包管理](./container-helm)、[kubectl 命令速查](/reference/kubectl-commands)、[云原生命令速查](/reference/cloudnative-commands)

### 官方文档

- Python 官方文档：https://docs.python.org/3/
- Python 下载与版本发布：https://www.python.org/downloads/
- requests 官方文档：https://requests.readthedocs.io/
- requests PyPI（看最新版本）：https://pypi.org/project/requests/
- paramiko 官网与文档：https://www.paramiko.org/
- paramiko changelog：https://www.paramiko.org/changelog.html
- APScheduler 文档：https://apscheduler.readthedocs.io/
- subprocess 官方文档：https://docs.python.org/3/library/subprocess.html
