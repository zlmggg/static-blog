# Ingress / 网格 / 服务连通排障详解：curl / grpcurl / nslookup / ipvsadm / nc

> 本文是 [云原生排障命令速查](../cloudnative-commands) 中「网络连通性（网格 / Ingress / 服务）」一组命令的从 0 到 1 详解，本篇一次讲清 `curl --resolve/-kv`、`grpcurl -plaintext list/调用`、`kubectl exec` 内 `nslookup` 验 CoreDNS、`ipvsadm -Ln`、`nc -uzv`。
> 目标：一个服务在集群里「别人访问不到」时，按「DNS → 端口 → HTTP → gRPC → kube-proxy 转发」这条链路从外到内逐层定位。
> 环境依据：curl 7.81（本机已装，`--resolve`/`-k`/`-v` 等据本机 `curl --help` 实跑确认）；nc 为 OpenBSD netcat（本机已装）；grpcurl 据其官方 README；kubectl/ipvsadm 据官方文档（本沙箱未装 K8s，对应示例标注「据官方文档」）。

## 一、命令是干什么的

服务连通排障的本质是一条**链路**，从外到内逐层验：

1. **DNS 解析对不对**？→ Pod 里 `nslookup 服务名` 验证 CoreDNS；
2. **端口通不通**？→ `nc -zv 主机 端口`（TCP）/`nc -uzv`（UDP）；
3. **HTTP 层对不对**？→ `curl -v` 看连接/TLS/状态码，`--resolve` 绕过 DNS 直连；
4. **gRPC 服务对不对**？→ `grpcurl`（普通 curl 搞不定二进制 gRPC）；
5. **kube-proxy 转发规则对不对**？→ `ipvsadm -Ln`（IPVS 模式看转发）。

> 类比：这是一张「报修 checklist」。用户说「打不开」，你别猜，按 DNS→端口→HTTP→gRPC→转发规则逐层试，哪一层断了就是哪一层的问题。

## 二、命令语法

```bash
curl [选项] URL
grpcurl [选项] 主机:端口 服务/方法
kubectl exec -it POD -- nslookup 名字
ipvsadm -Ln
nc [-uzv] 主机 端口
```

## 三、选项全表（对照本机 `curl --help` / `nc -h` / grpcurl 官方 README）

### 1. `curl`（本机实跑确认）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-v`，`--verbose` | 打印完整过程（DNS/TCP/TLS/请求响应头） | 排障首选，看卡在哪一步 |
| `-k`，`--insecure` | **跳过 TLS 证书校验** | 自签证书/域名不匹配时排查 |
| `--resolve host:port:addr` | 把指定 host+port **强行解析到某 IP** | 绕过 DNS，直接验证虚拟主机/多后端 |
| `-s`，`--silent` | 静默（不打进度条） | 脚本里 |
| `-o FILE` | 输出写文件 | 只要状态码 |
| `--connect-timeout SEC` | 连接超时 | 避免一直挂着 |
| `-r RANGE`，`--range` | 只取字节范围 | 测断点/大文件 |

> 本机 `curl --help all` 实跑确认：`-k, --insecure`、`--resolve <[+]host:port:addr...>`、`--connect-timeout` 均存在。

### 2. `grpcurl`（gRPC 版 curl）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-plaintext` | **不用 TLS**（明文） | 集群内 HTTP/2 明文 gRPC（最常用） |
| `list` | 列出服务端暴露的服务 | 先看有哪些服务 |
| `list 包.服务` | 列某服务的方法 | 看方法名 |
| `describe 符号` | 看方法/消息结构 | 不知道请求体长啥样 |
| `-d '{"k":v}'` | JSON 请求体（会转成 protobuf） | 调用时传参 |
| `-d @` | 请求体从 stdin 读 | 配合 here-doc/jq |
| `-H name:value` | 加 metadata/头 | 带鉴权 |
| `-proto`/`-import-path`/`-protoset` | 服务不支持 reflection 时，用 .proto 文件 | 无 reflection 的服务 |

> grpcurl 官方原话：「curl for gRPC」。服务端支持 **server reflection** 时，裸 `list`/`describe` 就能用；不支持就得给它 .proto 文件。

### 3. DNS / kube-proxy / nc

| 命令 | 作用 | 什么场景用 |
|---|---|---|
| `kubectl exec -it pod -- nslookup svc` | 在 Pod 内查集群 DNS | 验证 CoreDNS 解析 Service |
| `kubectl exec -it pod -- nslookup svc.ns.svc.cluster.local` | 用全限定名查 | 短名解析不了时看 FQDN |
| `ipvsadm -Ln` | 列 **IPVS** 虚拟服务器与转发规则 | kube-proxy=ipvs 模式看转发到哪些 Pod |
| `nc -zv 主机 端口` | 测 TCP 端口是否通（`-z` 扫描不发数据） | 端口连通性 |
| `nc -uzv 主机 端口` | 测 **UDP** 端口 | UDP 服务（如 DNS/QUIC） |

> `nc` 本机为 OpenBSD netcat（Debian patchlevel），支持 `-z`（zero-I/O 扫描）、`-u`（UDP）、`-v`（详细）。

## 四、由浅入深的典型示例

curl/nc 为本机可跑；kubectl/ipvsadm 示例「据官方文档」。

### 示例 1：用 curl -v 看完整连接过程

```bash
curl -v https://api.example.com/health
```

```text
*   Trying 1.2.3.4:443...
* Connected to api.example.com (1.2.3.4) port 443
* TLS handshake ...
> GET /health HTTP/1.1
< HTTP/1.1 200 OK
```

> `-v` 把「解析到哪个 IP → TCP 连上没 → TLS 握手 → 发请求 → 收到几几几」全打出来，断在哪一目了然。

### 示例 2：绕过 DNS 直连指定 IP（验证虚拟主机）

```bash
curl -v --resolve api.example.com:443:10.0.0.5 https://api.example.com/
```

> `--resolve` 让 `api.example.com:443` 直接解析到 `10.0.0.5`，绕过 DNS/负载均衡，专门验证「是不是某个后端节点的问题」。

### 示例 3：自签证书排障

```bash
curl -kv https://api.example.com/
```

> `-k` 跳过证书校验；如果加了 `-k` 就通、不加就报证书错，说明是 TLS 证书问题（域名不匹配/自签），不是服务不通。

### 示例 4：在 Pod 内验证 CoreDNS

```bash
kubectl exec -it api-pod -- nslookup payment
```

```text
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
Name:      payment
Address 1: 10.0.2.31 payment.default.svc.cluster.local
```

> 在业务 Pod 里查 Service 名，通了说明 CoreDNS 正常；查不到就是 DNS 配置问题。

### 示例 5：列 IPVS 转发规则

```bash
ipvsadm -Ln
```

```text
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight
TCP  10.96.15.20:80                rr
  -> 10.0.1.15:8080               Masq    1
  -> 10.0.2.31:8080               Masq    1
```

> kube-proxy=ipvs 模式下，Service VIP 被转发到哪些 Pod 后端，这里看得到。后端 IP 不对/缺漏就是 Service/Endpoints 问题。

### 示例 6：测 TCP / UDP 端口

```bash
nc -zv api-svc 8080
nc -uzv dns-svc 53
```

```text
Connection to api-svc 8080 port [tcp/*] succeeded!
```

> `-z` 只探测不发数据；UDP 加 `-u`。连不上就是网络策略/安全组/服务没监听。

### 示例 7：grpcurl 列出服务

```bash
grpcurl -plaintext order-svc:80 list
```

```text
order.Order
grpc.reflection.v1.ServerReflection
healthv1.Health
```

> 服务支持 reflection 时，直接列出 gRPC 服务。

### 示例 8：grpcurl 调用一个方法

```bash
grpcurl -plaintext -d '{"user_id":123}' order-svc:80 order.Order/GetOrder
```

```json
{
  "orderId": "A-1001",
  "status": "PAID"
}
```

> 普通 curl 调不动 gRPC（二进制 HTTP/2 protobuf）；网格里 gRPC 服务排障就用它。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `curl -v https://域名/` | 看连接全过程 |
| `curl -kv https://域名/` | 跳过证书查 TLS |
| `curl --resolve 域名:443:IP https://域名/` | 绕过 DNS 直连 |
| `kubectl exec pod -- nslookup svc` | 验 CoreDNS |
| `ipvsadm -Ln` | 看 IPVS 转发 |
| `nc -zv 主机 端口` | 测 TCP 端口 |
| `nc -uzv 主机 53` | 测 UDP 端口 |
| `grpcurl -plaintext 主机:端口 list` | 列 gRPC 服务 |
| `grpcurl -plaintext -d '{}' 主机:端口 包.服务/方法` | 调 gRPC |

## 六、RHEL 系与 Debian 系差异

- **curl/nc**：两系都有，用法一致；nc 有 OpenBSD 版（Debian/Ubuntu 默认）与 GNU 版（部分 RHEL），`-z/-u/-v` 基本通用；
- **ipvsadm**：Debian/Ubuntu 包 `ipvsadm`；RHEL/Rocky 同名；仅当 kube-proxy 跑 IPVS 模式才有规则，iptables 模式用 `iptables-save`；
- **grpcurl**：单二进制，两系一致；集群内明文用 `-plaintext`；
- kubectl exec 进哪个镜像，要确保镜像里有 `nslookup`/`nc`（精简镜像如 distroless 没有，得换 netshoot/busybox 调试 Pod）。

## 七、新手易错点

1. **逐层排查，别跳步**：先 DNS（nslookup）→ 端口（nc）→ HTTP（curl）→ gRPC（grpcurl）。一上来就 curl 容易误判是 DNS 问题还是服务问题。
2. **`--resolve` 只对 HTTP Host 验证有用**：它把指定 host:port 指向某 IP，适合验多后端/虚拟主机，不是万能。
3. **`-k` 是绕过证书校验**：排障用可以，但别拿来「治好」证书问题——根因是证书配置。
4. **精简镜像里没有 nslookup/nc**：业务容器是 distroless 时 exec 进去没有这些工具，改用临时调试 Pod（见 [kubectl-advanced](./kubectl-advanced)）。
5. **ipvsadm 只在 IPVS 模式有输出**：iptables 模式空，别误判「规则丢了」。
6. **危险提示**：`nc -z` 扫端口、`grpcurl` 调用都是真实打到服务；生产上别大范围扫、别误调写接口（带副作用的 RPC）。`--resolve` 临时改的是本机解析，不影响别人。

## 八、相关命令与文档

- 速查页：[云原生排障命令速查](../cloudnative-commands)
- 更细的 curl：[curl 详解](../cmd-net/curl)
- nc/端口扫描：[nc-telnet 详解](../cmd-net/nc-telnet)
- DNS 排障：[dig 详解](../cmd-net/dig)
- sidecar/网格控制面：[istioctl](./istioctl)
- Cilium 网络策略：[cilium](./cilium)
- 官方文档：curl https://curl.se/docs/manual.html ；grpcurl https://github.com/fullstorydev/grpcurl
