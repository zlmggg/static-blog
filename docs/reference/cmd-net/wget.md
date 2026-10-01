# wget 命令详解：下载文件与整站镜像（-O/-c/-q/-r/-np/-e proxy）

> 本文是 [网络命令速查](../network-commands#http-测试) 中 `wget` 的从 0 到 1 详解。
> 目标：掌握 `-O/-c/-q/-r/-np/-e use_proxy`，会下载、断点续传、整站镜像。
> 环境依据：本机实跑 **GNU Wget 1.21.2**（Ubuntu 22.04 自带；RHEL/Rocky 自带 1.21.x 用法一致）。

## 一、命令是干什么的

`wget`（World Wide Web get）是个**非交互式下载器**，专门从 HTTP/HTTPS/FTP 下载文件。和 `curl` 相比，它的特长是：**断点续传、递归整站抓取、后台下载、断网自动重试**。

> 类比：`curl` 像一个灵活的"请求瑞士军刀"，什么方法都能发；`wget` 像一个专注的"下载专员"——你给它一个链接，它就老老实实把文件拉下来，网络断了会自己重试、下到一半断了能接着下，还能把整个网站一层层镜像到本地。

什么时候用：
- 服务器上直接下个安装包/压缩包；
- 大文件下载到一半断了，续传；
- 把某个文档站整站镜像到本地离线看。

## 二、命令语法

```bash
wget [选项]... URL
```

- `[选项]`：控制存哪、是否续传、是否递归、代理等；
- `URL`：要下载的地址。

最简用法：

```bash
wget https://example.com/file.tar.gz
```

## 三、选项全表（对照 `wget --help`）

### 1. 基本下载

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-O 文件` | 保存为指定文件名（不用远程名） | `wget -O my.html URL` |
| `-c` | **断点续传**（接着没下完的继续） | 大文件断线后续传（极常用） |
| `-q` | 安静模式，不打印进度 | 脚本里 |
| `-b` | 下载完自动转后台 | 大文件不占着终端 |
| `-t N` | 重试次数（0 无限） | 弱网设大 |
| `-T 秒` | 超时时间 | 防卡死 |
| `-nc` | 已存在的文件不重复下 | 避免覆盖 |

### 2. 递归/镜像

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-r` | **递归**下载（顺着链接抓） | 镜像整站 |
| `-np`，`--no-parent` | **不向上**回溯到父目录 | 只抓某子目录，防止越抓越多 |
| `-l N` | 递归深度（默认 5） | 限制层数 |
| `-p` | 下载页面所需全部资源（图片/CSS） | 让镜像页面能正常显示 |
| `-k` | 把链接改成本地相对路径 | 离线可打开 |
| `-m` | 镜像模式（= `-r -N -l inf`） | 整站镜像快捷写法 |

### 3. 代理与认证

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-e use_proxy=yes -e https_proxy=...` | 命令行临时设代理 | 不走环境变量时 |
| `--proxy-user=用户 --proxy-password=密码` | 代理认证 | 内网代理 |
| `--http-user=用户 --http-password=密码` | HTTP 认证 | 要登录的下载 |
| `--no-check-certificate` | 跳过证书校验 | 自签名 |
| `--limit-rate=RATE` | 限速（如 `1M`） | 别把带宽占满 |

## 四、由浅入深的典型示例

以下输出为本机（GNU Wget 1.21.2）实跑。

### 示例 1：下载文件到当前目录

```bash
wget https://example.com/archive.tar.gz
```

> 会在当前目录生成 `archive.tar.gz`，并打印下载进度条、速度、大小。

### 示例 2：下载并指定文件名

```bash
wget -O /tmp/wtest.html https://example.com
```

```text
--2026-09-30 15:30:00--  https://example.com/
Connecting to ... connected.
HTTP request sent, awaiting response... 200 OK
Length: 713 [text/html]
Saving to: '/tmp/wtest.html'
```

> `-O` 直接写到指定文件。本例实跑得到一个 713 字节的 HTML。

### 示例 3：安静模式

```bash
wget -q -O /tmp/wtest.html https://example.com
```

> `-q` 不打印任何进度，适合脚本里静默下载。

### 示例 4：断点续传（大文件必备）

```bash
wget -c https://example.com/big.iso
```

> 下到一半 Ctrl+C 或断网后，再跑同样命令加 `-c`，会接着已下载的部分继续，不从头来。

### 示例 5：只检查链接是否存在（不真下）

```bash
wget --spider https://example.com
```

```text
Proxy request sent, awaiting response... 200 OK
Length: unspecified [text/html]
```

> `--spider` 只发 HEAD 看 URL 在不在、状态码多少，不存文件。

### 示例 6：递归镜像某文档目录

```bash
wget -r -np -k -p https://example.com/docs/
```

> `-r` 递归、`-np` 不往上跑到父目录、`-p` 带下图片资源、`-k` 改本地链接。把在线文档站离线存档。

### 示例 7：整站镜像快捷写法

```bash
wget -m -p -k https://example.com/
```

> `-m` 是镜像模式，等价于一组递归+时间戳选项，适合定期整站备份。

### 示例 8：通过代理下载

```bash
wget -e use_proxy=yes -e https_proxy=http://127.0.0.1:7890 https://example.com
```

> 没设代理环境变量时，用 `-e` 临时指定。也可以直接 `export https_proxy=...` 后正常用 wget。

### 示例 9：限速下载

```bash
wget --limit-rate=500k https://example.com/big.iso
```

> 把下载速度限制在 500KB/s，别在生产服务器上把带宽打满影响业务。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `wget URL` | 下载文件 |
| `wget -O 文件名 URL` | 存为指定名字 |
| `wget -c URL` | 断点续传 |
| `wget -q URL` | 静默下载 |
| `wget --spider URL` | 只检查链接 |
| `wget -r -np -p -k URL` | 递归镜像子目录 |
| `wget --limit-rate=500k URL` | 限速 |

## 六、RHEL 系与 Debian 系差异

`wget`（GNU Wget）两系都自带、用法一致。与 curl 的分工：

- `wget`：擅长下载/递归镜像/断点续传；
- `curl`：擅长任意 HTTP 方法、带头带 body、接口测试；
- 代理：两者都读 `http_proxy`/`https_proxy` 环境变量，wget 也可用 `-e` 临时指定。

## 七、新手易错点

1. **`-c` 才是续传**：不加 `-c` 重下会覆盖或报错，大文件务必 `-c`。
2. **`-O` 和 `-c` 别乱搭**：`-O` 指定新文件名时续传语义会变，续传一般用默认文件名。
3. **`-r` 不加 `-np` 会抓太多**：递归很容易顺着链接爬到无关目录，`-np` 限制在子目录内。
4. **递归抓公网站点要有度**：大规模镜像别人服务器可能被封 IP 或违反条款。
5. **`--spider` 不下载**：它只探测，别以为卡住。
6. **下载大文件用 `-b` 后台**：SSH 断开就没了，后台 + 日志更稳。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#http-测试)
- 灵活发请求/测接口：见 [curl](./curl)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
