# useradd、usermod、userdel、passwd、groupadd、id、whoami 命令详解：管理 Linux 用户和组

> 本文是 [Linux 命令速查](../linux-commands#用户与权限) 中 `useradd`/`usermod`/`userdel`/`passwd`/`groupadd`/`id`/`whoami` 的从 0 到 1 详解，本篇一次讲清「新增用户 / 改用户 / 删用户 / 改密码 / 加组 / 查自己是谁」。
> 目标：把各命令 `--help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `useradd --help` 就知道该用哪个选项。
> 环境依据：Ubuntu 22.04 自带 `passwd` 包（含 useradd/usermod/userdel/usergroupadd/passwd；RHEL/Rocky 对应 `shadow-utils` 包）；`id`/`whoami` 属 GNU coreutils 8.32。这些命令本身几乎不跨版本变化。

## 一、命令是干什么的

Linux 是多用户系统，每登录进来一个人，系统里都有一个「账号」记录他是谁、能进哪个目录、属于哪些组。这一组命令就是用来**增删改查账号**的：

- `useradd`：新建一个用户账号；
- `usermod`：修改已有用户（改家目录、改 shell、改附加组、锁账号等）；
- `userdel`：删除用户；
- `passwd`：设置/修改/锁定密码；
- `groupadd`：新建一个组；
- `id`：查看「我/某用户」的 UID、GID、所属组；
- `whoami`：只看当前登录的用户名。

> 类比：就像 Windows 里「设置 → 账户 → 家庭和其他用户」里新建/删除账号，只不过 Linux 用命令行做，而且账号信息存在 `/etc/passwd`、`/etc/group`、`/etc/shadow` 这几个纯文本文件里。

除 `id`、`whoami` 外，这些命令都要 **root 或 sudo** 才能执行（普通用户只能改自己的密码）。

## 二、命令语法

```bash
useradd [选项] 登录名
usermod [选项] 登录名
userdel [选项] 登录名
passwd [选项] [登录名]
groupadd [选项] 组名
id [选项]... [用户名]...
whoami
```

- 除 `id`/`whoami` 外，都要跟一个「用户名/组名」作为操作对象；
- `id` 不给用户名就查自己；`whoami` 永远只查自己；
- 不给选项时：`useradd 名字` 会建一个最小化账号（按 `/etc/login.defs` 默认值）；`passwd` 不带参数就是改自己的密码。

## 三、选项全表（对照各命令 `--help`）

### 1. useradd：新建用户

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-m`，`--create-home` | **创建家目录** `/home/名字` | 建人用账号时必加（很多发行版默认加） |
| `-M`，`--no-create-home` | 不建家目录 | 建只跑服务、不登录的账号 |
| `-d 目录`，`--home-dir 目录` | 指定家目录位置（默认 `/home/登录名`） | 想把家目录放到别处 |
| `-c 注释`，`--comment 注释` | GECOS 字段（一般写真名/备注） | 如 `useradd -c "张三" zhangsan` |
| `-s shell`，`--shell shell` | 指定登录 shell（如 `/bin/bash`、`/sbin/nologin`） | 服务账号给 `/sbin/nologin` 禁止登录 |
| `-g 组`，`--gid 组` | 指定**主组**（组名或 GID） | 想让主组不是默认同名组 |
| `-G 组1,组2`，`--groups 组1,组2` | 指定**附加组**列表 | 如加入 `docker`、`sudo` 组 |
| `-u UID`，`--uid UID` | 指定 UID 编号 | 集群里要固定 UID 时 |
| `-r`，`--system` | 建**系统账号**（UID 段不同、不建家目录、不过期） | 给服务用 |
| `-e 日期`，`--expiredate 日期` | 账号过期日期 `YYYY-MM-DD` | 临时工到期自动失效 |
| `-f 天数`，`--inactive 天数` | 密码过期后多少天禁用 | 密码策略 |
| `-p 加密串`，`--password 加密串` | 直接给一个**已加密**的密码串 | 脚本批量建号（别写明文） |
| `-N`，`--no-user-group` | 不建与用户同名的私有组 | 配合 `-g` 用 |
| `-U`，`--user-group` | 建与用户同名的组（默认行为） | 默认 |
| `-D`，`--defaults` | 查看/修改 useradd 默认配置 | `useradd -D` 看默认值 |

> 最常用就一句：`useradd -m -s /bin/bash 名字`，然后再 `passwd 名字` 设密码。

### 2. usermod：修改已有用户

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-a`，`--append` | **追加**附加组（必须配合 `-G`） | 加组时用 `usermod -aG docker 名字`，不加 `-a` 会把原附加组清空！ |
| `-G 组1,组2`，`--groups 组1,组2` | 重设附加组列表（覆盖式） | 配合 `-a` 才是追加 |
| `-l 新名`，`--login 新名` | 改登录名 | `usermod -l newold oldname` |
| `-L`，`--lock` | **锁定**账号（密码前加 `!`） | 临时不让某人登录 |
| `-U`，`--unlock` | 解锁账号 | 对应 `-L` |
| `-s shell`，`--shell shell` | 改登录 shell | 如改成 `/sbin/nologin` |
| `-d 目录`，`--home 目录` | 改家目录记录 | 配合 `-m` 才会真搬文件 |
| `-m`，`--move-home` | 把家目录内容搬到新位置（配合 `-d`） | 搬家目录时 |
| `-g 组`，`--gid 组` | 改主组 | 不常用 |
| `-u UID`，`--uid UID` | 改 UID | 慎用 |
| `-p 加密串`，`--password 加密串` | 改密码（加密串） | 脚本里用 |

### 3. userdel：删除用户

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-r`，`--remove` | **同时删家目录和邮箱** | 彻底删人（不加 `-r` 只删账号，家目录留着） |
| `-f`，`--force` | 强制删（即使用户仍登录中） | 危险，先确认没人在用 |

> 不带 `-r` 时，`/home/名字` 还在，里面的文件归属变成一串数字 UID；要连家目录一起清才加 `-r`。

### 4. passwd：密码与账号状态

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| （无参数） | 改**自己**的密码 | 日常用 |
| `名字` | root 改**别人**的密码 | `sudo passwd 名字` |
| `-l`，`--lock` | 锁定某用户密码 | 封号 |
| `-u`，`--unlock` | 解锁 | 对应 `-l` |
| `-d`，`--delete` | 删掉密码（变成空密码） | 仅限内网/实验 |
| `-e`，`--expire` | 强制下次登录改密码 | 新建号后 |
| `-S`，`--status` | 看密码状态（是否锁定、过期日） | `passwd -S 名字` |
| `-n 天数`，`--mindays` | 密码最少用多少天才能改 | 密码策略 |
| `-x 天数`，`--maxdays` | 密码最多多少天必须改 | 密码策略 |
| `-w 天数`，`--warndays` | 过期前几天开始提醒 | 密码策略 |

### 5. groupadd：新建组

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-g GID`，`--gid GID` | 指定 GID | 要固定编号时 |
| `-r`，`--system` | 建系统组 | 服务用 |
| `-f`，`--force` | 组已存在也不报错 | 脚本幂等 |

### 6. id / whoami：查身份

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-u`，`--user` | 只打印有效 UID 数字 | 脚本里取自己 UID |
| `-g`，`--group` | 只打印有效 GID | 取主组号 |
| `-G`，`--groups` | 打印**所有**组 ID | 看自己在哪些组 |
| `-n`，`--name` | 配合 `-u/-g/-G`，打印**名字**而不是数字 | `id -un` = 用户名 |
| `-r`，`--real` | 打印真实 ID 而非有效 ID | 较少用 |
| `-Z`，`--context` | 打印 SELinux 安全上下文 | RHEL 排查时 |

> `whoami` 没有选项，等价于 `id -un`。

## 四、由浅入深的典型示例

### 示例 1：看当前我是谁、在哪些组

```bash
id
```

```text
uid=1234(user) gid=1234(user) groups=1234(user)
```

逐段读：`uid=1234` 我的编号是 1234、`(user)` 名字叫 user；`gid=1234(user)` 主组是 user；`groups=` 后面列我加入的所有附加组（这里只有主组一个）。

```bash
whoami
```

```text
user
```

> 进了一堆容器/切来切去后，`whoami` 一秒确认「现在到底是哪个身份」，避免用 root 误操作。

### 示例 2：只取 UID 数字，给脚本用

```bash
id -u
id -un
id -G
```

```text
1234
user
1234
```

> `-u` 出数字、`-un` 出名字、`-G` 出所有组号。写 shell 脚本判断身份时常用 `id -u` 是否为 0 来判断是不是 root。

### 示例 3：查别人的身份

```bash
id root
```

```text
uid=0(root) gid=0(root) groups=0(root)
```

> root 的 UID 固定是 0。随便给个用户名就能查它的 UID/组，常用于排查「这个文件是谁的」。

### 示例 4：新建一个带家目录、能登录的用户

```bash
sudo useradd -m -s /bin/bash -c "Zhang San" zhangsan
sudo passwd zhangsan
```

> `-m` 建 `/home/zhangsan`；`-s /bin/bash` 给他能用的 shell；`-c` 写备注。`passwd` 会交互式提示输入两遍密码。这是建人的标准三步：`useradd` → `passwd` → （需要的话）加组。

### 示例 5：把用户加进 docker 附加组（最常踩坑）

```bash
sudo usermod -aG docker zhangsan
```

> `-a`（append）必须和 `-G` 一起用！如果只写 `usermod -G docker zhangsan`，zhangsan 原本的附加组会被**清空**，只剩 docker。加完组要重新登录（或 `newgrp docker`）才生效。

### 示例 6：锁定 / 解锁账号

```bash
sudo usermod -L zhangsan     # 锁定，他暂时登不进来
sudo passwd -S zhangsan      # 看状态
sudo usermod -U zhangsan     # 解锁
```

> `passwd -S` 输出第二列是密码状态：`P` 有可用密码、`L` 已锁定、`NP` 无密码。

### 示例 7：删除用户（连家目录一起清）

```bash
sudo userdel -r zhangsan
```

> 不加 `-r`，账号删了但 `/home/zhangsan` 和邮件还在；`-r` 才一并删掉。删之前确认他没有正在跑的进程。

### 示例 8：新建组并把人加进去

```bash
sudo groupadd devteam
sudo usermod -aG devteam zhangsan
```

> 建组后还是用 `usermod -aG` 把人追加进去。查一下：`id zhangsan` 应能看到 `devteam`。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `whoami` / `id` | 确认当前身份 |
| `id -u` | 脚本里判断是否 root（0 是 root） |
| `sudo useradd -m -s /bin/bash 名字` | 标准建号 |
| `sudo passwd 名字` | 设/改某人密码 |
| `sudo usermod -aG 组 名字` | **追加**附加组（别漏 `-a`） |
| `sudo usermod -L 名字` | 锁账号 |
| `sudo userdel -r 名字` | 连家目录一起删 |
| `sudo groupadd 组名` | 建组 |
| `passwd -S 名字` | 看密码状态 |

## 六、RHEL 系与 Debian 系差异

- **包名**：Ubuntu/Debian 这些命令都在 `passwd` 包；RHEL/CentOS/Rocky 在 `shadow-utils` 包。命令本身完全一样。
- **建号默认行为**：Ubuntu 上 `useradd` 默认**会**建家目录（配了 `USERGROUPS_ENAB`）；RHEL 上裸 `useradd 名字` 默认**不建**家目录，要手动加 `-m`。所以跨发行版建号一律带上 `-m` 最稳妥。
- **默认 shell**：新建用户默认 shell 一般是 `/bin/bash`（Ubuntu）或 `/bin/sh` 指向的 bash，差异不大，用 `-s` 显式指定最稳。
- `id`/`whoami` 是 coreutils，两系完全一致。

## 七、新手易错点

1. **`usermod -G` 不加 `-a` 会清空原有附加组**：这是最高频事故。加组永远用 `usermod -aG 组 用户`。
2. **改完组要重新登录才生效**：当前会话里 `id` 看不到新组，登出再登或 `newgrp 组名`。
3. **`userdel` 不加 `-r` 家目录不会删**：删人后磁盘还占着，记得加 `-r`（但先备份重要文件）。
4. **`useradd -p` 要的是加密后的密码，不是明文**：脚本里可用 `openssl passwd -6 密码` 生成，别直接写明文。
5. **服务账号给 `/sbin/nologin`**：只想让它跑服务、不让人登录的账号，建号时 `-s /sbin/nologin`，别给 bash。
6. **`id -u` 是 0 才是 root**：脚本里别用 `whoami = root` 判断，因为有的容器里 root 用户名可能不叫 root，但 UID 一定是 0。
7. **危险：删用户前确认他没在跑进程**：`userdel -f` 会强删仍登录的用户，可能影响业务，先 `pkill -u 名字` 或确认。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 权限位怎么读、怎么改：见 [chmod](./chmod)
- 文件属主怎么改：见 [chown](./chown)
- 提权临时当 root：见 [sudo 与 su](./sudo-su)
- 更细粒度的授权：见 [setfacl](./setfacl)
- 用户/组概念专题：[Linux 用户与组](../../guide/linux-users)
