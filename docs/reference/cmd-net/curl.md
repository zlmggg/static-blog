# curl 命令详解：万能 HTTP 请求与接口测试

> 本文是 [网络命令速查](../network-commands#http-测试) 中 `curl` 的从 0 到 1 详解。
> 目标：把 `-X/-H/-d/-o/-I/-i/-k/-v/-x/-u/-w/-L/--resolve` 这些高频选项讲清楚，测接口、下文件、排 HTTP 问题时随手就来。
> 环境依据：本机实跑 **curl 7.81.0**（OpenSSL 3.0.2，Ubuntu 22.04 自带；RHEL/Rocky 8/9 自带 7.6x~7.76，核心选项一致）。

## 一、命令是干什么的

`curl`（client URL）是个全能的 URL 传输工具，能通过 HTTP/HTTPS/FTP 等协议收发数据。SRE 用它最多的场景是**测 Web 接口**：发 GET/POST、带头、带 body、看状态码和耗时、走代理、跳过证书校验。

> 类比：浏览器是给人看网页的，`curl` 是给命令行"发请求"的——你让它请求哪个 URL、用什么方法、带什么头、body 是什么，它就原封不动发出去，把服务器回的内容打给你。Postman 能做的大部分事，curl 一行命令就能做。

什么时候用：
- 后端接口开发完，命令行快速验证返回；
- 线上某 URL 不通，用 `-v` 看卡在哪一步（DNS？TCP？TLS？）；
- 批量下载文件、测接口耗时和状态码。

## 二、命令语法

```bash
curl [选项]... URL
```

- `[选项]`：请求方法、请求头、body、输出、各种开关；
- `URL`：请求地址，必填。

最简用法：

```bash
curl https://example.com      # GET 并把响应体打到屏幕
```

## 三、选项全表（对照 `curl --help`）

### 1. 请求方法与请求体

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-X 方法` | 指定 HTTP 方法（GET/POST/PUT/DELETE） | 发 POST/PUT 时 |
| `-d 数据` | 发送请求体（带它默认变 POST） | 提交表单/JSON |
| `-H "头: 值"` | 加请求头（可多次用） | 设 `Content-Type`、`Authorization` |
| `-A "UA"` | 设 User-Agent | 伪装客户端 |
| `-u 用户:密码` | HTTP Basic 认证 | 带账号密码 |
| `-e URL` | 设 Referer | 模拟来源页 |

### 2. 响应与输出

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-o 文件` | 响应体**存到文件**而不是屏幕 | 下载到指定文件名 |
| `-O` | 用 URL 里的文件名存盘 | 批量下载 |
| `-I` | 只取**响应头**（HEAD 请求） | 看状态码/响应头 |
| `-i` | 响应**头 + 体**一起显示 | 想看头又想看体 |
| `-s` | 安静模式（不显示进度条/错误） | 脚本里 |
| `-w 格式` | 打印自定义变量（状态码、耗时） | 测性能/取状态码 |
| `-L` | **自动跟随重定向** | 301/302 跳转到目标 |

### 3. 排障与连接控制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v` | **详细过程**（连接、TLS、请求/响应头） | 不通时排障首选 |
| `-k` | **跳过 HTTPS 证书校验** | 自签名证书测试 |
| `-x 代理` | 指定 HTTP/SOCKS 代理 | `curl -x http://127.0.0.1:7890 URL` |
| `--resolve 主机:端口:IP` | 强制把某域名解析到指定 IP | 测本地服务但域名是线上的 |
| `-m 秒` | 最大超时 | 防止挂死 |
| `-4` / `-6` | 强制 IPv4 / IPv6 | 排协议族 |
| `-f` | HTTP 错误码（4xx/5xx）时静默失败 | 脚本里判定失败 |

## 四、由浅入深的典型示例

以下输出为本机（curl 7.81.0）实跑（经环境代理访问公网）。

### 示例 1：GET 一个 URL，打印响应体

```bash
curl -sS https://example.com
```

> 不加 `-sS` 会附带进度条；`-s` 安静、`-S` 出错仍提示。日常把响应体存文件用 `-o`。

### 示例 2：只看响应头

```bash
curl -sS -I https://example.com
```

```text
HTTP/2 200
date: Wed, 30 Sep 2026 15:29:34 GMT
content-type: text/html; charset=utf-8
server: cloudflare
cf-cache-status: HIT
```

> `-I` 发 HEAD 请求，只拿回响应头。看服务是 Nginx 还是 Cloudflare、缓存命中没有。

### 示例 3：响应头 + 响应体

```bash
curl -sS -i https://example.com
```

> 头部那几行是响应头，后面才是 HTML 正文。调试接口时常用。

### 示例 4：保存到文件

```bash
curl -sS -o /tmp/page.html https://example.com
```

> `-o` 指定保存路径。等价于 `wget -O`。

### 示例 5：POST JSON 接口

```bash
curl -sS -X POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  -d '{"name":"sre","age":35}'
```

```text
{
  "args": {},
  "data": "{\"name\":\"sre\",\"age\":35}",
  "headers": {
    "Content-Type": "application/json",
    "Host": "httpbin.org",
    "User-Agent": "curl/7.81.0"
  },
  "json": { "age": 35, "name": "sre" },
  "url": "https://httpbin.org/post"
}
```

> `-X POST` 指定方法，`-H` 设 JSON 头，`-d` 是 body。返回里的 `json` 段说明服务端正确收到了 JSON。

### 示例 6：看详细连接过程（排障）

```bash
curl -sS -v -o /dev/null https://example.com
```

```text
* Uses proxy env variable https_proxy == 'http://...proxy...:8080'
*   Trying 10.4.146.145:8080...
* Connected to (nil) (10.4.146.145) port 8080 (#0)
* Establish HTTP proxy tunnel to example.com:443
> CONNECT example.com:443 HTTP/1.1
> Host: example.com:443
< HTTP/1.1 200 Connection Established
```

> `-v` 把每一步都打出来：`*` 是 curl 自身过程，`>` 是发出的请求，`<` 是收到的响应。不通时一眼看出卡在哪。

### 示例 7：只看状态码和耗时（监控常用）

```bash
curl -sS -o /dev/null -w "http_code=%{http_code} time_total=%{time_total}s size=%{size_download}\n" https://example.com
```

```text
http_code=200 time_total=2.226940s size=713
```

> `-w` 用变量输出想要的指标，`-o /dev/null` 丢掉正文。做健康检查/压测前量接口耗时的标准写法。

### 示例 8：跟随重定向

```bash
curl -sS -o /dev/null -w "final_url=%{url_effective} code=%{http_code}\n" -L http://example.com
```

```text
final_url=http://example.com/ code=200
```

> 不加 `-L`，遇到 301/302 就停在跳转页；加 `-L` 才会一路跟到最终 URL。`%{url_effective}` 显示最终落到哪。

### 示例 9：跳过证书校验 / 走代理

```bash
curl -k https://自签名服务
curl -x http://127.0.0.1:7890 https://example.com
```

> `-k` 信任自签名证书（别在生产随便用）；`-x` 显式指定代理。

### 示例 10：强制解析到指定 IP

```bash
curl --resolve example.com:443:203.0.113.9 https://example.com
```

> 不改本机 hosts，就让 curl 把 `example.com` 指到 `203.0.113.9`，常用于切流前验证某台后端。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `curl -sS URL` | GET 取正文 |
| `curl -I URL` | 只看响应头 |
| `curl -o 文件 URL` | 下载到文件 |
| `curl -X POST -H "Content-Type: application/json" -d '{...}' URL` | POST JSON |
| `curl -v URL` | 看连接全过程排障 |
| `curl -w "%{http_code} %{time_total}\n" -o /dev/null -s URL` | 取状态码+耗时 |
| `curl -L URL` | 跟随重定向 |
| `curl -k URL` | 跳过证书校验 |

## 六、RHEL 系与 Debian 系差异

`curl` 两系都自带、用法一致。注意点：

- 老版本 curl 不支持 `--http3`、某些新 `--aws-sigv4` 选项，以本机 `curl --help all` 为准；
- 通过代理时，curl 自动读 `http_proxy`/`https_proxy` 环境变量（本例环境即是如此）；
- 与 `wget` 区别：curl 更灵活（任意方法、带头），wget 更擅长递归下载。

## 七、新手易错点

1. **`-d` 默认就是 POST**：写 `-d 'a=1'` 不用再 `-X POST`，但加 JSON 时 `-X POST` 更清晰。
2. **POST JSON 一定要带 `Content-Type: application/json`**：不带的话服务端可能按表单解析。
3. **HTTPS 自签名报错先加 `-k` 测试**：但 `-k` 关闭了校验，生产别依赖。
4. **不加 `-L` 拿不到最终内容**：301 跳转后默认不跟，结果是个跳转页。
5. **`-w` 的变量要包在引号里**：否则 shell 会把 `%{...}` 当占位符展开。
6. **`-v` 输出里 `<`/`>`/`*` 含义不同**：`>` 请求、`<` 响应、`*` curl 自身日志。
7. **敏感 `-u user:pass` 会进 shell 历史**：避免明文写密码。

## 八、相关命令与文档

- 速查页：[网络命令速查](../network-commands#http-测试)
- 下载文件/递归抓取：见 [wget](./wget)
- 测端口连通：见 [nc 与 telnet](./nc-telnet)
- 查域名解析：见 [dig](./dig)
- 网络整体原理：见 [Linux 网络专题](../../guide/linux-network)
