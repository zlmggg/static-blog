# setfacl 与 getfacl 命令详解：比 chmod 更细的访问控制列表

> 本文是 [Linux 命令速查](../linux-commands#用户与权限) 中 `setfacl`/`getfacl` 的从 0 到 1 详解。
> 目标：把 setfacl 的常用选项和 ACL 条目写法讲清楚，并和 `chmod` 对比，看完你知道「什么时候该用 ACL 而不是 chmod」。
> 环境依据：本机未安装 `acl` 包，本文选项与示例依据 man-pages 官方手册 setfacl(1)（man7.org，2026 年快照）核实；包名在 Debian/Ubuntu 为 `acl`，RHEL/CentOS/Rocky 同为 `acl`。

## 一、命令是干什么的

`chmod` 的权限只有三档：**属主 / 属组 / 其他人**。但现实经常是：

- 我想让用户 `lisa` 能读这个文件，可她既不是属主、也不在属组里——chmod 做不到（除非把她加进组）。
- 我想让「一个目录里新建的文件自动带上某个权限规则」——chmod 也做不到。

**ACL（Access Control List，访问控制列表）** 就是来补这个缺口的：它允许你**额外**给**指定的某几个用户/某几个组**单独授权，不受「属主/属组/其他人」三档限制。

- `setfacl`：给文件设置/修改/删除 ACL 规则；
- `getfacl`：查看一个文件现在的 ACL 规则。

> 类比：chmod 像是「门的总钥匙」——只有房主、家人、外人三类人；ACL 像是「给某几个特定同事单独配的门禁卡」，可以精确到某个人，还能规定门禁卡的有效期式规则。

## 二、命令语法

```bash
setfacl [-bkndRLP] [{-m|-x} acl_spec] [{-M|-X} acl_file] 文件...
getfacl 文件...
```

- `-m`：**修改/新增**一条 ACL（要带权限）；
- `-x`：**删除**一条 ACL；
- `-b`：清空所有扩展 ACL；
- `-d`：对**默认 ACL**（目录里新建文件继承的规则）操作；
- `-R`：递归；
- `acl_spec` 格式：`[d:]u:用户名:权限`、`[d:]g:组名:权限`、`[d:]m:权限`、`[d:]o:权限`。

## 三、选项全表（依据 setfacl(1) 官方手册）

### 1. 增删改 ACL

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-m acl_spec`，`--modify` | **新增/修改**一条 ACL（必须带权限） | 最常用：`setfacl -m u:lisa:r 文件` |
| `-x acl_spec`，`--remove` | **删除**某条 ACL（不带权限） | `setfacl -x g:staff 文件` |
| `-M acl_file` | 从**文件**读 ACL 规则来批量改 | 配合 getfacl 备份恢复 |
| `-X acl_file` | 从文件读要删除的条目 | 批量删 |
| `--set acl_spec` | **整体替换** ACL（旧的全清，重设） | 要完全重写时 |
| `-b`，`--remove-all` | 删除所有**扩展** ACL，保留属主/属组/其他人基础位 | 恢复成纯 chmod 控制 |
| `-k`，`--remove-default` | 删除**默认 ACL** | 目录不再让新文件继承 |

### 2. 行为控制

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-d`，`--default` | 操作**默认 ACL**（新建文件继承的规则） | 给目录设继承 |
| `-R`，`--recursive` | 递归应用到目录树下 | 批量设 ACL |
| `-n`，`--no-mask` | **不**自动重算 effective mask | 调试时 |
| `--mask` | 强制重算 effective mask | 显式控制 mask |
| `--test` | **只演练**，不真改，打印结果 | 先试错不翻车 |
| `-L`/`-P` | 递归时是否跟随软链接 | `-P` 不跟随 |
| `--restore=文件` | 恢复之前 `getfacl -R` 备份的权限 | 灾难恢复 |

### ACL 条目格式（重点）

```text
[d:]u:用户名:权限     # 给某个命名用户授权
[d:]g:组名:权限       # 给某个命名组授权
[d:]m::权限           # effective rights mask（有效权限上限）
[d:]o::权限           # 其他人
```

- `d:` 前缀 = 默认 ACL（继承用）；
- 权限用 `r`/`w`/`x` 组合，或数字（r=4,w=2,x=1）；
- 设了命名用户/命名组后，系统会自动补一条 mask，mask 决定这些额外条目的「有效权限上限」。

## 四、由浅入深的典型示例

> 以下示例依据 setfacl(1) 官方手册及常用实践；本机未安装 acl 包，未实跑输出，仅作语法示范。

### 示例 1：额外给某个用户读权限

```bash
setfacl -m u:lisa:r file
```

> 意思是：在 chmod 的三档之外，**额外**让用户 lisa 对 `file` 有读权限。她不需要是属主、也不需要被加进任何组。设完用 `getfacl file` 能看到多了一行 `user:lisa:r--`。

### 示例 2：撤销某命名组的 ACL

```bash
setfacl -x g:staff file
```

> 把之前给 `staff` 组加的 ACL 规则删掉。删一个不存在的条目不报错。

### 示例 3：用 mask 收回所有额外用户/组的写权限

```bash
setfacl -m m::rx file
```

> mask 是「有效权限上限」。把 mask 设成 `rx`，那么所有命名用户/命名组实际能拿到的权限都不会超过 rx——即使它们各自写着 `rwx`。这是批量收权的技巧。

### 示例 4：把一个文件的 ACL 复制给另一个

```bash
getfacl file1 | setfacl --set-file=- file2
```

> 用管道把 `file1` 的 ACL 喂给 `file2`，让两者 ACL 完全一致。

### 示例 5：设默认 ACL，让目录里新建的文件自动继承

```bash
setfacl -d -m u:lisa:rwX dir
```

> `-d` 设默认 ACL：以后在 `dir` 里新建的文件/子目录，会自动带上「lisa 可读写」的规则。这是 chmod 完全做不到的——多人协作目录的标准做法。

### 示例 6：递归给整个目录树设 ACL

```bash
setfacl -R -m u:lisa:rwX projects/
setfacl -R -d -m u:lisa:rwX projects/
```

> 第一行：`-R` 递归，给现有所有文件让 lisa 可读写；第二行：`-d` 默认 ACL，保证以后新建的文件也自动授权。两条配合才完整。

### 示例 7：查看 ACL（getfacl）

```bash
getfacl file
```

```text
# file: file
# owner: root
# group: user
user::rw-
user:lisa:r--
group::r--
group:staff:rwx          #effective:r-x
mask::r-x
other::r--
```

> 注意 `#effective:r-x`：虽然 staff 写着 rwx，但 mask 是 r-x，所以 staff 实际有效权限被 mask 压到 r-x。这就是 mask 的作用。

### 示例 8：清空所有扩展 ACL，回到纯 chmod

```bash
setfacl -b file
```

> `-b` 把所有额外加的命名用户/组 ACL 全删掉，文件回到只有属主/属组/其他人三档。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `setfacl -m u:用户:rwx 文件` | 额外给某用户授权 |
| `setfacl -m g:组:r-x 目录` | 额外给某组授权 |
| `setfacl -x u:用户 文件` | 删掉某用户的 ACL |
| `setfacl -R -m u:用户:rwX 目录` | 递归给现有文件授权 |
| `setfacl -R -d -m u:用户:rwX 目录` | 让新文件自动继承授权 |
| `getfacl 文件` | 查看 ACL |
| `setfacl -b 文件` | 清空扩展 ACL |

## 六、RHEL 系与 Debian 系差异

- 包名都叫 `acl`，装法：Debian/Ubuntu `apt install acl`，RHEL/CentOS/Rocky `yum install acl`。
- **文件系统要支持 ACL**：现代 ext4/xfs 默认都带 ACL 挂载选项，一般不用管；老内核或特殊挂载可能要加 `acl` 挂载参数。
- 两系命令行为一致。RHEL 开 SELinux 的环境下，ACL 之外还有一层 SELinux 规则，别把两者搞混。

## 七、新手易错点

1. **`ls -l` 看不到完整 ACL**：设了 ACL 后，权限位最后会多一个 `+`（如 `-rw-r--r--+`），但具体规则要 `getfacl` 才看得到。
2. **mask 会「压缩」权限**：明明给了 rwx，实际却只有 r-x，多半是 mask 太低。这是 ACL 最反直觉的点。
3. **默认 ACL 只影响「新建」文件**：`-d` 设的规则不会回溯改已有文件，已有文件还要单独 `-R -m`。
4. **别用 ACL 当主权限机制**：ACL 很灵活，但也让权限模型变复杂。能用 chown+组解决的就别上 ACL，ACL 是补充不是替代。
5. **`setfacl -b` 不会删基础权限**：它只删扩展 ACL，属主/属组/其他人那三位还在。
6. **危险：递归设 ACL 前先 `--test`**：`setfacl --test -R -m ... 目录` 先演练，确认要改的文件清单对了再真跑。
7. **备份权限再操作**：`getfacl -R 目录 > acl.bak`，搞砸了用 `setfacl --restore=acl.bak` 恢复。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#用户与权限)
- 基础三档权限：见 [chmod](./chmod)
- 改属主/属组：见 [chown](./chown)
- 官方手册：[setfacl(1) - man7.org](https://man7.org/linux/man-pages/man1/setfacl.1.html)、[getfacl(1)](https://man7.org/linux/man-pages/man1/getfacl.1.html)
- 权限与安全模型专题：[Linux 用户与组](../../guide/linux-users)、[Linux 安全](../../guide/linux-security)
