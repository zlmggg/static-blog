---
title: 用户、权限与认证
description: Linux 用户与组、文件权限、特殊权限、ACL、sudo 提权与集中认证，含 RHEL/Debian 差异
category: Linux
difficulty: 中级
---
# 用户、权限与认证

::: tip 本篇定位
讲清三件事：**用户和组怎么管理、文件权限怎么控制、普通用户怎么安全地获得管理员能力**。
这是 Linux 安全的地基——绝大多数"访问被拒绝"的问题，最终都能回到 UID/GID、权限位、特殊权限或 PAM/SELinux 上。
:::

## 先建立全局观：AAA 模型

几乎所有软件级安全方案都遵循 **AAA** 流程：

| 环节 | 英文 | 解决的问题 |
|---|---|---|
| 认证 | **A**uthentication | 你是谁？（校验用户名/密码、密钥） |
| 授权 | **A**uthorization | 你能做什么？（权限、sudo 规则） |
| 审计 | **A**uditing / Accounting | 你做过什么？（日志记录，`/var/log/secure`） |

Linux 本地账号体系正是按这个思路：登录时认证（PAM）→ 操作时按 UID/GID 授权 → 全程写日志。

---

## 一、用户与组的核心概念

### 1.1 为什么需要"用户"

Linux 是**多用户多任务**系统，多个用户可同时使用同一台机器。用户机制带来三样东西：

1. **身份标识**：每个进程、文件都归属某个用户；
2. **资源隔离**：A 用户默认不能动 B 用户的文件；
3. **责任追溯**：配合日志，知道是谁做的操作。

::: warning 生产环境别长期直接用 root
初学时常直接用 root 图省事，但 root 权限不受限制，一个误操作（如 `rm -rf /路径`）可能毁掉系统。
生产环境应使用普通账号 + `sudo` 提权。
:::

### 1.2 UID 与 GID

- 登录成功后系统会发一块"令牌 token"，包含用户标识和组成员信息；
- 每个用户通过 **UID（User ID）** 唯一标识，每个组通过 **GID（Group ID）** 唯一标识；
- 用户名/组名只是给人看的，系统真正识别的是数字 ID。

**用户分类（以 RHEL/CentOS/Rocky 为例）：**

| 类型 | UID | 用途 |
|---|---|---|
| 管理员 root | `0` | 超级用户 |
| 系统用户 | `1–999`（CentOS 6 以前是 1–499） | 给守护进程/服务使用，通常不能登录 |
| 登录用户 | `1000+`（CentOS 6 以前是 500+） | 给人交互登录 |

> Ubuntu/Debian 的划分基本一致：系统用户 1–999，普通用户从 1000 开始。
> 默认普通用户 UID 上限约 60000，但创建时可用 `-u` 指定更大的值（执行时会有提示，不影响成功）。

**用户组分类：**

| 类型 | GID |
|---|---|
| root 组 | `0` |
| 系统组 | `1–999` |
| 普通组 | `1000+` |

### 1.3 主组与附加组

- **主组（primary group）**：每个用户**必须有且只有一个**主组。默认创建用户时会自动建一个同名组作为主组，因组内只有该用户，也称**私有组**；
- **附加组（supplementary group）**：一个用户可以属于 0 个或多个附加组，用于批量获得额外权限（如加入 `wheel`/`sudo` 组才能管理员提权）。

### 1.4 用 id 查看身份

```bash
id              # 查看当前用户
id root         # 用户id=0(root) 组id=0(root) 组=0(root)
id zhangsan     # 用户id=1000 组id=1000(zhangsan) 组=1000(zhangsan),10(wheel)
id -u zhangsan  # 只看 UID
id -gn zhangsan # 只看主组名
```

输出中 `组=` 后面：第一个是主组，逗号后是所有附加组。

---

## 二、用户和组的配置文件

四个核心文件：

| 文件 | 内容 | 默认权限 |
|---|---|---|
| `/etc/passwd` | 用户及其属性（名称、UID、主 GID、家目录、Shell） | `644`（所有人可读） |
| `/etc/shadow` | 用户密码哈希及密码策略 | `000`/`600`（仅 root 读） |
| `/etc/group` | 组及其属性 | `644` |
| `/etc/gshadow` | 组密码及管理员 | `000`/`600` |

::: tip 为什么密码要单独放 shadow
早期密码哈希在 passwd 里，而 passwd 所有人可读，攻击者可离线破解哈希。
后来把哈希移到仅 root 可读的 shadow（称为 shadow-utils），passwd 里密码位只留一个 `x`。
:::

### 2.1 /etc/passwd 字段

```bash
getent passwd zhangsan
zhangsan:x:1000:1000:张三:/home/zhangsan:/bin/bash
```

| 字段 | 示例 | 含义 |
|---|---|---|
| 用户名 | zhangsan | 登录名，建议 ≤8 位、无特殊符号 |
| 密码位 | `x` | 真实哈希在 shadow；`x` 表示用 shadow |
| UID | 1000 | 用户标识号 |
| GID | 1000 | **主组**标识号 |
| 描述(GECOS) | 张三 | 备注信息，可空 |
| 家目录 | /home/zhangsan | 登录后默认所在目录 |
| 登录 Shell | /bin/bash | 登录后使用的 Shell；`/sbin/nologin` 表示禁止登录 |

### 2.2 /etc/shadow 字段

```bash
root:$6$xxxx....:19000:0:99999:7:::
```

| 字段 | 示例 | 含义 |
|---|---|---|
| 用户名 | root | |
| 密码哈希 | `$6$...` | `$6$`=SHA-512；`$1$`=MD5；空=免密登录；`!`/`*`=**锁定，不能登录** |
| 最后改密时间 | 19000 | 从 1970-01-01 起的天数 |
| 最小间隔 | 0 | 两次改密最少间隔天数 |
| 最大间隔 | 99999 | 密码有效天数 |
| 警告时间 | 7 | 到期前多少天警告 |
| 不活动期限 | 空 | 过期后仍保留的宽限天数 |
| 失效时间 | 空 | 账号绝对失效日期（天数） |

> 密码位前出现 `!`（如 `!$6$...`）即被锁定；连续两个 `!` 或 `!!` 通常是新建未设密码的系统用户。

### 2.3 /etc/group 与 /etc/gshadow

```bash
getent group web
web:x:1008:zhangsan,lisi
```

group 字段：`组名:组密码位(x):GID:组成员列表`（成员用逗号分隔，不含以该组为主组的用户）。

gshadow 字段：`组名:组密码哈希:组管理员:组成员列表`。组密码用于用户通过 `newgrp` 临时加入非自己所在的组，实际很少用。

---

## 三、用户组管理

### 3.1 groupadd 新建组

```bash
groupadd web              # 新建组，GID 自动分配
groupadd -g 1086 dba      # 指定 GID
groupadd -r sysops        # 新建系统组（GID<1000）
groupadd -f web           # 已存在不报错、直接退出
```

常用选项：`-g` 指定 GID；`-r` 系统组；`-f/--force` 已存在则成功退出。

### 3.2 groupmod 修改组

```bash
groupmod -g 2087 dba      # 改 GID
groupmod -n dba-new dba   # 改组名（-n 新名 旧名）
```

### 3.3 groupdel 删除组

```bash
groupdel dba-new          # 删除空组
groupdel -f dba-new       # 强制删除（即使是某用户主组，会导致该用户无有效主组）
```

> 不能删除某个用户的**主组**（除非 -f）；要先把该用户改到别的主组。

### 3.4 gpasswd：管理组成员和组密码

```bash
gpasswd -a zhangsan web       # 加入用户
gpasswd -d zhangsan web       # 移除用户
gpasswd -M zhangsan,lisi web  # 批量设置成员（覆盖）
gpasswd -A zhangsan web       # 设置组管理员
gpasswd web                   # 给组设密码
```

### 3.5 groupmems：管理附加组成员

```bash
groupmems -g web -l           # 列出 web 组成员
groupmems -g web -a zhangsan  # 添加
groupmems -g web -d zhangsan  # 删除
groupmems -g web -p           # 清空成员
```

> Ubuntu 下用 groupmems 增删成员可能要求输入当前用户密码，RHEL 下通常不需要。

---

## 四、用户管理

### 4.1 useradd 创建用户

```bash
useradd zhangsan                      # 按默认配置创建
useradd -u 1100 -g dba -G wheel web   # 指定 UID、主组、附加组
useradd -d /data/zhangsan zhangsan    # 指定家目录
useradd -s /sbin/nologin app          # 不允许登录（服务账号）
useradd -r nginx                      # 系统用户
useradd -c "运维张三" zhangsan         # 加描述
useradd -e 2026-12-31 zhangsan        # 指定失效日期
```

常用选项：

| 选项 | 作用 |
|---|---|
| `-u` | 指定 UID |
| `-g` | 指定主组（组名/GID，须已存在） |
| `-G` | 指定附加组，多个用逗号 |
| `-d` | 指定家目录 |
| `-s` | 指定登录 Shell |
| `-m` / `-M` | 强制建 / 不建家目录 |
| `-r` | 创建系统用户 |
| `-c` | 描述信息（GECOS） |
| `-e` / `-f` | 失效日期 / 过期宽限天数 |

**创建后默认会：** 新建同名私有组、（在 RHEL 上）建家目录并把 `/etc/skel` 里的模板文件复制进去：

```bash
ls -a /home/zhangsan
.  ..  .bash_logout  .bash_profile  .bashrc  .mozilla  .zshrc
```

### 4.2 RHEL 与 Ubuntu/Debian 的关键差异

::: warning 重点差异：useradd 默认不建家目录
- **RHEL/CentOS/Rocky**：`useradd zhangsan` 默认**会创建家目录**；
- **Ubuntu/Debian**：`useradd zhangsan` 默认**不创建家目录**，必须加 `-m`：
  ```bash
  useradd -m zhangsan
  ```
:::

**更推荐的做法：**

- **Ubuntu/Debian 用 `adduser`**（交互式 Perl 脚本）：自动建家目录、设密码、复制 skel，更友好：
  ```bash
  adduser zhangsan
  ```
- 注意 RHEL 上的 `adduser` 只是 `useradd` 的软链接，**没有交互**，别混淆。

### 4.3 默认配置从哪来

| 文件 | 控制内容 |
|---|---|
| `/etc/default/useradd` | useradd 默认值（家目录根、Shell、是否建邮箱等），`useradd -D` 查看 |
| `/etc/login.defs` | UID/GID 范围、密码有效期、umask、加密算法等全局默认 |
| `/etc/skel/` | 新建用户家目录的模板文件（想给每个新用户放初始配置就放这里） |
| `/etc/motd` | 用户登录后显示的欢迎信息 |

```bash
useradd -D                 # 查看默认配置
useradd -D -s /bin/sh      # 修改默认 Shell
grep -vE '^#|^$' /etc/login.defs   # 查看生效的全局策略
```

### 4.4 usermod 修改用户

```bash
usermod -s /bin/bash zhangsan      # 改 Shell
usermod -d /data/zs -m zhangsan    # 改家目录并迁移内容（-m 一起用）
usermod -g dba zhangsan            # 改主组
usermod -aG wheel zhangsan         # 追加附加组（-a 追加，务必和 -G 一起，否则覆盖）
usermod -c "新描述" zhangsan
usermod -l newname oldname         # 改登录名
usermod -L zhangsan                # 锁定（shadow 密码前加 !）
usermod -U zhangsan                # 解锁
```

::: danger 改附加组一定加 -a
`usermod -G group user` 会**覆盖**现有附加组，可能导致用户丢掉原有组（如 wheel）。
追加请用 `usermod -aG group user`。
:::

### 4.5 userdel 删除用户

```bash
userdel zhangsan          # 删除用户，保留家目录
userdel -r zhangsan       # 同时删除家目录和邮件
userdel -f zhangsan       # 强制，即使用户已登录
```

> 正在使用中的用户默认无法删除（`user xxx is currently used by process N`）；
> `-f` 强删后，该用户的进程要等其退出才真正消失。

### 4.6 newusers 批量创建

准备文件，每行一个用户，格式 `用户名:密码:UID:GID:描述:家目录:Shell`：

```bash
cat > users.txt <<'EOF'
u1:123456:1024:1024::/home/u1:/bin/bash
u2:123456:1025:1025::/home/u2:/bin/bash
EOF
newusers users.txt
```

---

## 五、密码管理

### 5.1 passwd 改密码

```bash
passwd                # 改自己的密码
passwd zhangsan       # root 改指定用户密码
```

**非交互式（脚本里用）：**

```bash
# RHEL/CentOS/Rocky 支持 --stdin
echo 'NewPass123' | passwd --stdin zhangsan

# Ubuntu/Debian 不支持 --stdin，统一用 chpasswd
echo 'zhangsan:NewPass123' | chpasswd
```

设置密码时若太简单会提示（仅警告，root 可强制设置）：
- `无效的密码：密码少于 8 个字符`
- `无效的密码：密码未通过字典检查 - 太简单或太有规律`
- `抱歉，密码不匹配`（两次输入不一致）

### 5.2 chpasswd 批量改密

```bash
chpasswd < passwd.txt          # 文件每行 用户名:密码
echo 'zhangsan:123456' | chpasswd
chpasswd -e < users.txt        # -e：密码已是加密哈希，直接写入
```

### 5.3 密码策略

- 基础有效期策略在 `/etc/login.defs`（PASS_MAX_DAYS / PASS_MIN_DAYS / PASS_WARN_AGE）；
- 复杂度（长度、大小写、数字、特殊字符）由 **PAM** 的 `pam_pwquality`（RHEL）/ `pam_cracklib` 控制，配置在 `/etc/security/pwquality.conf`。

### 5.4 生成强随机密码

```bash
openssl rand -base64 12                  # 推荐
tr -dc 'A-Za-z0-9!@#$%^&*' < /dev/urandom | head -c 12; echo
mkpasswd -m sha-512 123456               # 生成哈希
```

---

## 六、文件权限

### 6.1 权限的两个维度

**维度一：针对谁（ugo）**

| 对象 | 英文 | 含义 |
|---|---|---|
| u | User / Owner | 文件所有者（创建者），权限最高 |
| g | Group | 文件所属组的所有成员 |
| o | Others | 既不是所有者也不在所属组的其他人 |
| a | All | 以上全部 |

**维度二：能做什么（rwx）**

| 权限 | 数字 | 对**文件** | 对**目录** |
|---|---|---|---|
| r（读） | 4 | 可查看文件内容 | 可列出目录下的文件（ls） |
| w（写） | 2 | 可修改文件内容 | 可在目录中新建/删除/重命名文件 |
| x（执行） | 1 | 可执行该文件 | 可进入该目录（cd） |

::: tip 目录权限是高频考点
- 目录的 `x` 决定能不能**进入**（cd）；没有 x，连 r 都无法正常使用；
- 目录的 `w` 决定能不能**增删里面的文件**（能否删一个文件看的是**所在目录**的 w，不是文件本身的权限！）；
- 记忆："r 看里面有什么，w 增删里面的东西，x 能进去"。
:::

### 6.2 查看权限 ls -l

```bash
ls -l /etc/bashrc
-rw-r--r--. 1 root root 2696 9月 23 06:13 /etc/bashrc
```

权限串 `-rw-r--r--.` 拆解：

- 第 1 位 `-`：文件类型（`-`普通文件、`d`目录、`l`软链接、`s`套接字、`c/b`设备）；
- 第 2–4 位 `rw-`：所有者权限；
- 第 5–7 位 `r--`：所属组权限；
- 第 8–10 位 `r--`：其他人权限；
- 最后的 `.`/`+`：`.`表示有 SELinux 安全上下文，`+`表示设置了 ACL。

### 6.3 chown：改属主/属组

```bash
chown zhangsan file.txt          # 只改属主
chown :dba file.txt              # 只改属组
chown zhangsan:dba file.txt      # 同时改（推荐写法）
chown -R zhangsan:dba /dir       # 递归
chown --reference=f1 f2          # 参照 f1 的归属设置 f2
```

### 6.4 chgrp：只改属组

```bash
chgrp dba file.txt
chgrp -R dba /dir
```

### 6.5 chmod：改权限

**数字法（最常用）：** 把 ugo 三个数字相加

```bash
chmod 755 script.sh    # rwxr-xr-x：所有者全权，其他人读+执行
chmod 644 file.txt     # rw-r--r--：所有者读写，其他人只读
chmod 600 key.pem      # rw-------：仅所有者可读写（密钥常用）
chmod 777 dir          # 所有人全权（生产慎用）
```

**符号法（精确增删）：**

```bash
chmod u+x script.sh    # 所有者加执行
chmod g-w file.txt     # 组去掉写
chmod o=r file.txt     # 其他人设为只读（覆盖）
chmod a+r file.txt     # 所有人加读
chmod u+r,g-x file.txt # 同时指定
```

符号含义：`u/g/o/a` + `+`(加) / `-`(减) / `=`(覆盖) + `r/w/x`。

### 6.6 root 不受权限限制

- r/w 对 root 无效：即使文件是 000，root 仍可读写；
- 只要所有者、组、其他人**三者之一有 x**，root 就能执行；
- 所以 `ls -l /etc/shadow` 显示 000，root 照样能打开。

---

## 七、默认权限 umask

### 7.1 什么是 umask

新建文件/目录时，系统会给一个"起始权限"，再用 **umask（权限掩码）** 屏蔽掉一些位：

- 普通文件起始 `666`（rw-rw-rw-，默认不给执行）；
- 目录起始 `777`（rwxrwxrwx）。

**默认 umask 通常是 `022`：**

```bash
文件：666 - 022 = 644   # rw-r--r--
目录：777 - 022 = 755   # rwxr-xr-x
```

::: warning 这里是"掩码"不是简单减法
当 umask 含奇数位时，直接相减可能出错，应理解为"**把 umask 中为 1 的位从起始权限里去掉**"。
例如文件 666 与 umask 027：结果是 640（rw-r-----），而不是 639。
:::

### 7.2 查看与修改

```bash
umask              # 查看（022）
umask -S           # 符号显示 u=rwx,g=rx,o=rx
umask 027          # 临时修改（仅当前会话）
( umask 666; touch f.txt )   # 子 Shell 临时生效，不影响当前会话
```

永久生效写入用户的 `~/.bashrc` / `~/.profile`。

---

## 八、特殊权限 SUID / SGID / Sticky

除了 rwx，还有三个特殊权限，位于权限串的特殊位置：

| 特殊权限 | 数字 | 显示位置 | 作用对象 |
|---|---|---|---|
| **SUID**（Set User ID） | 4 | 所有者的 x 位 | 可执行文件 |
| **SGID**（Set Group ID） | 2 | 所属组的 x 位 | 文件或目录 |
| **Sticky**（粘滞位） | 1 | 其他人的 x 位 | 目录 |

### 8.1 SUID

```bash
ls -l /usr/bin/passwd
-rwsr-xr-x 1 root root ... /usr/bin/passwd      # 所有者 x 位变成 s
```

- **作用**：用户执行带 SUID 的程序时，**临时以文件所有者（常是 root）的身份**运行；
- **典型例子**：`/usr/bin/passwd` 有 SUID，普通用户改密码时程序临时获得 root 权限，才能写入只有 root 能改的 `/etc/shadow`；
- 显示：所有者有 x 加 SUID 显示 `s`，没有 x 显示 `S`。

```bash
chmod u+s /usr/bin/cat     # 加 SUID
chmod 4755 program         # 数字法（前面加 4）
chmod u-s /usr/bin/cat     # 去掉
```

::: danger SUID 是高危项
SUID 程序若有漏洞或能被利用（如 `cat` 被加 SUID，普通用户就能读 /etc/shadow），等于变相提权。
安全基线会扫描所有异常 SUID 文件：`find / -perm -4000 -type f 2>/dev/null`。
:::

### 8.2 SGID

- **对文件**：执行时临时以**文件所属组**身份运行（类似 SUID）；
- **对目录（更常用）**：在该目录下新建的文件**自动继承目录的属组**，方便组协作。

```bash
chmod g+s /shared          # 目录加 SGID
chmod 2770 /shared         # 数字法（前面加 2）
```

效果：在 /shared 下新建文件，属组自动是 /shared 的组，而不是创建者的私有组。

### 8.3 Sticky 粘滞位

```bash
ls -ld /tmp
drwxrwxrwt 18 root root ... /tmp      # 其他人 x 位变成 t
```

- **作用**：目录设了 Sticky 后，文件**只有其所有者、目录所有者或 root 才能删除/重命名**；
- 防止多人共用目录时互相删对方文件，`/tmp` 就是典型。

```bash
chmod o+t /shared          # 加 Sticky
chmod 1777 /shared         # 数字法（前面加 1）
```

### 8.4 特殊权限组合数字

| 权限组合 | 前缀数字 |
|---|---|
| SUID | 4xxx |
| SGID | 2xxx |
| Sticky | 1xxx |
| SUID+SGID+Sticky | 7xxx |

---

## 九、文件特殊属性 chattr / lsattr

特殊权限之外，ext4/xfs 文件还支持一组**文件属性**，用 `chattr` 设置、`lsattr` 查看，连 root 也受其约束。

```bash
chattr +i /etc/resolv.conf     # 加"不可修改"
lsattr /etc/resolv.conf
chattr -i /etc/resolv.conf     # 去掉
```

| 属性 | 作用 | 典型用途 |
|---|---|---|
| `i`（immutable） | 不可修改：不能删除、重命名、改内容、建链接 | 保护关键配置不被误改 |
| `a`（append） | 只能**追加**数据，不能删除或修改已有内容 | 日志文件防篡改 |
| `A` | 访问不更新 atime | 减少磁盘 IO |
| `S` | 同步写入（不缓存） | 重要文件 |
| `u` | 删除时保留数据可恢复 | 防误删 |

::: tip 常见排障
明明是 root、权限也够，却提示 `Operation not permitted` 无法修改/删除文件，先 `lsattr 文件` 看是否被加了 `i` 或 `a` 属性。
:::

---

## 十、ACL 细粒度权限

UGO 只能给"一个所有者 + 一个组"授权，若要给**多个指定用户/组分别授权**（如让 zhangsan 读写、lisi 只读），需要 **ACL（Access Control List）**。

```bash
# 给指定用户加权限（rwx）
setfacl -m u:zhangsan:rw file.txt
# 给指定组加权限
setfacl -m g:dba:r file.txt
# 查看
getfacl file.txt
# 递归 + 给目录设"默认 ACL"（新建文件自动继承）
setfacl -R -m d:u:zhangsan:rwx /dir
# 删除某条 ACL / 清空全部
setfacl -x u:zhangsan file.txt
setfacl -b file.txt
```

设置 ACL 后 `ls -l` 权限串末尾会显示 `+`。

::: warning 用 ACL 需文件系统支持
ACL 要求挂载的文件系统支持 POSIX ACL（现代 ext4/xfs 默认支持）。
mask 项会限制附加用户/组的实际最大权限，改 ACL 后注意 mask 是否被重置。
:::

---

## 十一、sudo 提权

### 11.1 为什么用 sudo

- 不用把 root 密码告诉每个需要管理权限的人；
- 可**精细控制**某个用户只能执行哪些命令；
- 每次提权默认有日志，满足审计。

用户要能用 sudo，通常需加入指定组：RHEL 的 `wheel`、Debian/Ubuntu 的 `sudo`。

### 11.2 配置方式

**永远用 `visudo` 编辑**（会做语法检查，写错可能导致 sudo 失效）：

```bash
visudo                       # 编辑 /etc/sudoers
visudo -f /etc/sudoers.d/zhangsan   # 推荐：单独文件，便于管理
```

授权语法：

```text
用户/组  来源主机=(以谁的身份)  命令
```

示例：

```text
zhangsan ALL=(ALL) ALL                  # zhangsan 可执行所有命令（需输自己的密码）
%wheel   ALL=(ALL) ALL                  # wheel 组成员可执行所有命令
zhangsan ALL=(ALL) NOPASSWD: ALL        # 免密码（自动化/个人常用）
zhangsan ALL=(ALL) /usr/bin/systemctl restart nginx   # 只允许这一条
```

> 组以 `%` 开头；多条命令用逗号分隔；命令写**完整路径**更安全。

### 11.3 常用操作与别名

```bash
sudo systemctl restart nginx     # 以 root 执行单条命令
sudo -i                          # 切换到 root 的登录 Shell
sudo -u app whoami               # 以指定用户身份执行
sudo -l                          # 查看当前用户被授予的权限
```

sudoers 里还可用 `User_Alias`、`Cmnd_Alias` 把一批用户/命令归类。sudo 操作记录在 `/var/log/secure`（RHEL）或 `/var/log/auth.log`（Ubuntu）。

---

## 十二、集中认证 LDAP（了解）

当服务器成百上千台时，每台都维护本地账号不现实，需要**集中认证**：

- **LDAP**（常用 389/636 端口，开源实现 OpenLDAP）：统一存放用户/组，多台机器登录时到 LDAP 校验；
- **Active Directory（AD）**：微软的目录服务，企业内网常见；
- 客户端通过 **SSSD** 或 `nslcd` 接入，配合 PAM/NSS 完成认证与信息查询。

与本地账号区别：本地账号信息在 `/etc/passwd`；LDAP 用户在目录服务器，本地文件里没有。

> 现代更流行用 SSO（OIDC/SAML，如 Keycloak、Authentik）统一登录 Web 服务，原理类似。

---

## 十三、登录相关日志与命令

| 命令/文件 | 作用 |
|---|---|
| `who` / `w` | 当前谁在线、在做什么 |
| `last` | 历史登录记录（读 /var/log/wtmp） |
| `lastlog` | 各用户最后一次登录时间 |
| `/var/log/secure` | **RHEL** 认证、sudo、登录日志 |
| `/var/log/auth.log` | **Ubuntu/Debian** 对应日志 |
| `/var/log/audit/audit.log` | auditd 审计日志（更细） |

排查"谁登录过、认证为何失败"时，先看上述日志。

---

## 面试自测

1. Linux 中文件和目录的 r、w、x 权限有什么区别？（重点说目录）
2. 能否删除一个文件由什么权限决定？（**所在目录的 w+x**，不是文件本身）
3. SUID、SGID、Sticky 分别解决什么问题？各举一个系统自带例子（passwd / 组协作目录 / tmp）。
4. umask 027 下，新建文件和目录的权限分别是多少？
5. `usermod -G` 和 `-aG` 的区别？
6. 为什么密码哈希放在 /etc/shadow 而不是 /etc/passwd？
7. root 想改文件却提示 Operation not permitted，可能是什么原因？（chattr +i / +a）

## 相关速查

- [Linux 命令速查](/reference/linux-commands)
- [网络命令速查](/reference/network-commands)
