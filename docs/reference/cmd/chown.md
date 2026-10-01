# chown 命令详解：改文件和目录的属主与属组

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `chown`（含 `chgrp`）的从 0 到 1 详解。
> 目标：把 `chown --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `chown --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。`chgrp` 是 coreutils 里改属组的独立小命令。

## 一、命令是干什么的

`chown` = **change owner**（改变属主），用来改一个文件/目录「归谁所有」。

`ls -l` 看到的 `-rw-r--r-- 1 root root` 里，第一个 `root` 是**属主(owner)**，第二个 `root` 是**属组(group)**。`chown` 就是改这两个的。

- 改属主：`chown 用户名 文件`；
- 同时改属主和属组：`chown 用户名:组名 文件`；
- 只改属组：`chown :组名 文件` 或 `chgrp 组名 文件`；
- 递归改一整个目录：`chown -R 用户名:组名 目录`。

> 类比：就像 Windows 右键文件 → 属性 → 安全 → 高级里「更改所有者」。Linux 文件除了权限位，还必须明确「这东西归谁」——属主天然拥有 chmod/chown 之外的大部分决定权。
>
> 注意：**改属主需要 root 权限**（普通用户只能在自己拥有的文件上改组，且组必须是自己所在的组）。

## 二、命令语法

```bash
chown [选项] [属主][:[属组]] 文件...
chown [选项] --reference=参考文件 文件...
chgrp [选项] 组名 文件...
```

- `属主`：要改成的用户名（或 UID 数字）；
- `:属组`：跟在冒号后，要改成的组名；冒号前属主省略 = 只改组；
- 只写 `属主:`（带冒号）会把属组一起改成该用户的登录组；
- `chgrp 组名 文件` 等价于 `chown :组名 文件`。

## 三、选项全表（对照 `chown --help`）

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-R`，`--recursive` | **递归**改目录下所有内容 | 改整个目录归属（最常用） |
| `-v`，`--verbose` | 每个文件都打印处理过程 | 想看它改了哪些 |
| `-c`，`--changes` | 只在真的变了时才报告 | 比 `-v` 安静 |
| `-f`，`--silent`，`--quiet` | 压制大部分错误 | 脚本里 |
| `--reference=RFILE` | 用参考文件的属主/组 | 不手写用户名 |
| `--from=当前属主:当前组` | **只改当前匹配**的文件 | 如只把 root 拥有的改成 user，`chown --from=root user 目录` |
| `-h`，`--no-dereference` | 改**软链接本身**而不是它指向的文件 | 默认会跟着链接走 |
| `-H`/`-L`/`-P` | 配合 `-R` 时如何对待软链接 | `-P` 默认不跟随；较少细究 |
| `--preserve-root` | 对 `/` 递归时拒绝执行 | 安全保护 |

> 属主和属组都可以写数字 UID/GID。`chown 1000:1000 文件` 和 `chown user:user 文件` 效果一样。

## 四、由浅入深的典型示例

### 示例 1：改文件属主

```bash
touch c.txt
ls -l c.txt
sudo chown root c.txt
ls -l c.txt
```

```text
-rw-r--r-- 1 user user 0 Sep 30 23:34 c.txt
-rw-r--r-- 1 root user 0 Sep 30 23:34 c.txt
```

> 第一列属主从 `user` 变成 `root`，属组还是 `user`。改属主必须 root（所以前面加 sudo）。

### 示例 2：同时改属主和属组

```bash
sudo chown root:root c.txt
ls -l c.txt
```

```text
-rw-r--r-- 1 root root 0 Sep 30 23:34 c.txt
```

> `属主:属组` 一起写，两个都变。这是最常用的完整写法。冒号也可以用点 `.`（`root.root`），但冒号更清晰。

### 示例 3：只改属组

```bash
sudo chown :user c.txt
ls -l c.txt
```

```text
-rw-r--r-- 1 root user 0 Sep 30 23:34 c.txt
```

> 属主省略、冒号后写组名 = 只改组。属主还是 root，属组变回 user。

### 示例 4：用 chgrp 只改组

```bash
sudo chgrp user c.txt
ls -l c.txt
```

```text
-rw-r--r-- 1 root user 0 Sep 30 23:34 c.txt
```

> `chgrp 组名 文件` 是 `chown :组名 文件` 的等价写法，语义更直白。

### 示例 5：递归改整个目录的归属

```bash
sudo mkdir -p deep && sudo touch deep/x deep/y
sudo chown -R user:user deep
ls -l deep
```

```text
-rw-r--r-- 1 user user 0 Sep 30 23:34 x
-rw-r--r-- 1 user user 0 Sep 30 23:34 y
```

> `-R` 把目录本身和里面所有文件一起改成 `user:user`。解压 zip/拷贝文件后属主常是 root，要用它把整个目录还给业务用户。

### 示例 6：让文件归属跟某个参考文件一致

```bash
sudo chown --reference=c.txt deep/x
```

> 不手写用户名，让 `deep/x` 的属主和属组跟 `c.txt` 一模一样。批量统一归属时省事。

### 示例 7：只改「当前是某属主」的文件

```bash
sudo chown --from=root user deep/ -R
```

> `--from=root` 表示：只把**现在属主是 root** 的文件改成 user，其他不动。比盲目 `-R` 精准，不易误伤。

### 示例 8：Web 服务目录的标准归属

```bash
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html
```

> 部署 Web 时，网站文件要让 nginx/apache（www-data 用户）能读，所以把整个目录属主改成 www-data。一般不直接给 777，而是靠正确的属主 + 合理权限。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `chown 用户 文件` | 只改属主 |
| `chown 用户:组 文件` | 同时改属主和属组（**最常用**） |
| `chown :组 文件` | 只改属组 |
| `chgrp 组 文件` | 只改属组（更直白） |
| `chown -R 用户:组 目录` | 递归改目录树归属 |
| `chown --from=root 用户 目录` | 只改属主是 root 的文件 |
| `chown --reference=参考 文件` | 照着别的文件改归属 |

## 六、RHEL 系与 Debian 系差异

`chown`/`chgrp` 属 coreutils，**两系用法完全一致**。仅有的细微点：

- Web 服务运行用户不同：Ubuntu 是 `www-data`，RHEL/CentOS 是 `nginx`/`apache`，改属主时名字别写错；
- 其他没有实质差异。

## 七、新手易错点

1. **改属主要 root**：普通用户 `chown` 别人的文件会报 `Operation not permitted`，记得加 sudo。
2. **`chown 用户 文件` 不改组**：只写用户名、不写冒号，属组保持不变。想一起改组就 `用户:组`。
3. **`-R` 要小心路径**：`chown -R user:user /` 会把整个系统归属改乱，永远别对 `/` 递归。确认路径再回车。
4. **冒号别漏成空格**：`chown root root file` 是错的（chown 只认第一个位置参数），要用 `root:root`。
5. **改完权限不生效先看属主**：有时候是属主不对导致「我明明在文件上有 rw 却写不进去」，先 `ls -l` 看属主。
6. **软链接默认跟着走**：`chown` 默认改的是软链接**指向**的目标，不是链接本身；想改链接自己要加 `-h`。
7. **危险：`chown -R` 误改系统目录**：把 `/etc`、`/usr` 递归改错属主可能搞坏系统，递归操作前先 `ls` 确认目标。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#文件与目录)
- 改权限位（rwx）：见 [chmod](./chmod)
- 细粒度授权：见 [setfacl](./setfacl)
- 新建用户/组：见 [用户管理](./user-mgmt)
- 提权：见 [sudo 与 su](./sudo-su)
- 权限与属主概念专题：[Linux 用户与组](../../guide/linux-users)
