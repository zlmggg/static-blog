# timedatectl、chronyc 与 ntpq 详解：查时区、对时间、看 NTP 同步状态

> 本文是 [Linux 命令速查](../linux-commands#时间与定时) 中 `timedatectl`、`chronyc`、`ntpq` 的从 0 到 1 详解。
> 目标：把 `timedatectl status/set-timezone/set-ntp`、`chronyc sources/tracking`、`ntpq -p` 的输出讲清楚，多看几遍后，你在服务器上敲 `timedatectl status` 就知道时间有没有同步。
> 环境依据：`timedatectl` 属 systemd（systemd 249，Ubuntu 22.04 自带）；`chronyc` 属 chrony 包、`ntpq` 属 ntp 包（本机沙箱未安装，选项与输出依据 chrony 官方文档与 NTP 官方 man，示例为示意）。

## 一、命令是干什么的

时间同步对服务器至关重要（日志排序、证书、分布式系统都依赖准确时间）。三个命令分工：

- **`timedatectl`**：systemd 提供的**系统时间/时区总管**，一条命令看当前时间、时区、NTP 是否开启，也能改时区、开关 NTP。
- **`chronyc`**：chrony 这个 NTP 实现的**控制工具**，`sources` 看同步了哪些时间源、`tracking` 看同步精度。现代发行版（RHEL 8+/Ubuntu 20.04+）默认用 chrony。
- **`ntpq`**：传统 `ntpd` 的查询工具，`-p` 列出所有 NTP 对等节点的状态。老系统或仍用 ntpd 的环境用它。

> 类比：`timedatectl` 像"系统时间的中控台"；`chronyc`/`ntpq` 像"对时手机的信号强度面板"——看你到底跟哪台对时服务器对得上、误差多大。

## 二、命令语法

```bash
# timedatectl
timedatectl [命令]...
# chronyc
chronyc [子命令]
# ntpq
ntpq -p
```

- `timedatectl` 不带参数 = `status`；
- `chronyc sources`/`tracking` 是最常用的两个子命令；
- `ntpq -p`（peers）列出对等节点。

## 三、选项全表（对照 `--help` 与官方文档）

### 1. timedatectl 子命令

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `status` | 显示当前时间设置（默认） | 一眼看时间/时区/NTP 状态 |
| `set-time 时间` | 手动设置系统时间 | 一般不手动，用 NTP |
| `set-timezone 时区` | 设置时区（如 `Asia/Shanghai`） | 改时区 |
| `list-timezones` | 列出所有可用时区 | 不知道时区名时 |
| `set-ntp BOOL` | 开启/关闭网络时间同步 | `set-ntp true` 开自动对时 |
| `set-local-rtc BOOL` | RTC 是否用本地时间 | 双系统时谨慎 |
| `timesync-status` | 看 systemd-timesyncd 状态 | 用内置 timesyncd 时 |

### 2. chronyc 常用子命令

| 子命令 | 中文含义 | 什么场景用 |
|---|---|---|
| `sources` | 列出所有时间源及选中状态 | 看跟谁对时（最常用） |
| `tracking` | 显示当前时钟性能参数 | 看误差、偏移、层（最常用） |
| `sourcestats` | 各时间源的统计（漂移率等） | 深入分析 |
| `makestep` | 立即跳转校时 | 偏移太大时手动跳 |
| `rtcdata` | 看硬件时钟 | 较少用 |

### 3. ntpq 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-p` | 列出所有 peers（对等节点） | 看 NTP 节点状态（最常用） |
| `-n` | 不做域名解析，直接显示 IP | 不想反查时 |
| `-c 命令` | 执行交互式命令 | 脚本里调用 |

## 四、由浅入深的典型示例

### 示例 1：timedatectl 看整体状态

```bash
timedatectl status
```

示意输出（在正常 systemd 机器上；本沙箱无 systemd，以下为典型输出）：

```text
               Local time: Wed 2026-09-30 23:28:36 CST
           Universal time: Wed 2026-09-30 15:28:36 UTC
                 RTC time: Wed 2026-09-30 15:28:37
                Time zone: Asia/Shanghai (CST, +0800)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

逐行看：

- `System clock synchronized: yes`：**时间已同步**（关键）；
- `NTP service: active`：NTP 服务在跑；
- `Time zone`：当前时区；
- `RTC in local TZ: no`：硬件时钟用 UTC（推荐）。

### 示例 2：改时区为上海

```bash
sudo timedatectl set-timezone Asia/Shanghai
```

> 不知道时区名就先 `timedatectl list-timezones | grep Shanghai`。

### 示例 3：开启/关闭 NTP 自动同步

```bash
sudo timedatectl set-ntp true
```

> 开启后 systemd 会拉起 chronyd（或 timesyncd）自动对时；`false` 关闭。

### 示例 4：chronyc 看时间源

```bash
chronyc sources
```

示意输出（依据 chrony 官方文档）：

```text
MS Name/IP address         Stratum Poll Reach LastRx Last sample
===============================================================================
^* ntp.aliyun.com                2   9   377    42   -123us[ -130us] +/-  45ms
^+ cn.ntp.org.cn                 2  10   377    50   +200us[ +210us] +/-  60ms
^? time.cloudflare.com           3   6   377    10   -500us[ -510us] +/- 100ms
```

逐列看：

- `M` 列的符号：`^*` 是**当前选中**的最佳源；`^+` 是备选；`^?` 是暂未选中/不可达；
- `Stratum`：层，1 最接近原子钟，越小越好；
- `Reach`：八进制，`377` 表示最近 8 次轮询都成功；变成 `0` 说明连不上；
- `Last sample`：与时间源的偏移，单位 us/ms。

### 示例 5：chronyc 看同步精度

```bash
chronyc tracking
```

示意输出（依据 chrony 官方文档）：

```text
Reference ID    : CB00710F (ntp.aliyun.com)
Stratum         : 2
System time     : 0.000006523 seconds slow of NTP time
Last offset     : -0.000006747 seconds
RMS offset      : 0.000035822 seconds
Frequency       : 3.225 ppm slow
Leap status     : Normal
```

- `Stratum 2`：对上了一个二级源；
- `System time`：当前系统钟慢了 6.5 微秒；
- `Leap status: Normal`：没有闰秒异常。

### 示例 6：ntpq -p 看对等节点

```bash
ntpq -p
```

示意输出（依据 NTP 官方 man 常见格式）：

```text
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
*ntp.aliyun.com  .GPS.            1 u   42 1024  377    2.345   -123.4   0.045
+cn.ntp.org.cn   .PPS.            1 u   50 1024  377    5.678   +200.1   0.060
```

逐列看：

- 第一列符号：`*` 当前选中、`+` 备选、`-` 被排除、`x` 伪造源、`?` 不可达；
- `st`：stratum 层；
- `when`/`poll`：上次/下次查询间隔；
- `reach`：八进制可达位；
- `delay`/`offset`/`jitter`：网络延迟、时钟偏移、抖动。

### 示例 7：偏移太大，强制立即校时

```bash
sudo chronyc makestep
```

> 平时 chrony 是慢慢把钟"挪"到正确时间（slew）；偏移太大时用 `makestep` 直接跳过去。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `timedatectl status` | 看时间/时区/NTP 是否同步（**最常用**） |
| `timedatectl set-timezone Asia/Shanghai` | 改时区 |
| `timedatectl set-ntp true` | 开自动对时 |
| `chronyc sources` | 看同步了哪些时间源 |
| `chronyc tracking` | 看同步精度和层 |
| `chronyc makestep` | 立即跳转校时 |
| `ntpq -p` | 传统 ntpd 的节点状态 |

## 六、RHEL 系与 Debian 系差异

- **默认 NTP 实现**：RHEL/CentOS/Rocky 8+ 和 Ubuntu 20.04+ 默认都用 **chrony**（`chronyd` + `chronyc`）；老 RHEL 6/7 或老 Debian 可能用 **ntpd**（`ntpq`）。
- Ubuntu 最小安装可能只带 `systemd-timesyncd`（由 `timedatectl timesync-status` 查看），轻量但功能少；生产服务器建议装 chrony。
- 时区配置文件：`/etc/localtime`（软链到 `/usr/share/zoneinfo/...`），两系一致。
- 改时区两系统一用 `timedatectl set-timezone`，不要手动 `cp` 时区文件。

## 七、新手易错点

1. **容器里 `timedatectl` 报错**：容器通常没有 systemd 作为 PID 1，`timedatectl` 连不上 bus；容器时间一般跟随宿主机，不用自己对。
2. **`chronyc`/`ntpq` 不加 sudo 也能查**：一般普通用户可读，但某些受限环境要 sudo。
3. **`Reach` 变成 0**：说明到时间源的网络不通（防火墙/安全组挡了 UDP 123）。
4. **手动 `date -s` 设时间**：开了 NTP 后会被立刻校回，要永久改请用 NTP。
5. **时区设错导致日志时间对不上**：排查线上问题前先 `timedatectl status` 确认时区是 `Asia/Shanghai`。
6. **RTC in local TZ 应为 no**：双系统（装了 Windows）时若 Windows 把硬件钟当本地时间，Linux 会乱，用 `timedatectl set-local-rtc 1` 处理。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#时间与定时)
- 显示/计算时间：`date`（详解见 [date](./date)）
- 定时任务：`crontab`（详解见 [crontab](./crontab)）
- 定时任务原理：见 [Linux 定时任务](../../guide/linux-cron)
