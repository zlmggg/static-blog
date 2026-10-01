# zip 与 unzip 命令详解：处理 Windows 风格的 .zip 压缩包

> 本文是 [Linux 命令速查](../linux-commands#压缩与打包) 中 `zip`、`unzip` 的从 0 到 1 详解。
> 目标：把 `zip -r` 打包、`unzip -l` 列内容、`unzip -d` 解包到指定目录讲清楚，多看几遍后，你在服务器上敲 `zip -r` 就知道怎么压一个目录。
> 环境依据：Info-ZIP zip 3.0 / unzip 6.00（Ubuntu 22.04 自带；RHEL/Rocky 自带同属 Info-ZIP，用法一致）。

## 一、命令是干什么的

Windows 上最常见的压缩格式是 `.zip`，Linux 用 `zip`/`unzip` 处理它。和 `tar` 的区别：

- `zip`：**打包+压缩一步到位**，生成 `.zip`；
- `unzip`：解开 `.zip`。

和 `tar` 对比：`tar` 是"打包可选压缩"，且 `.tar.gz` 在 Windows 上不如 `.zip` 通用；给 Windows 用户传压缩包，用 `zip` 最省事。

> 类比：`zip` 就是 Linux 版的"发送到→压缩(zipped)文件夹"。

## 二、命令语法

```bash
# 打包
zip [选项] 包名.zip [要打包的文件或目录]...
# 解包
unzip [选项] 包名.zip [要解的文件]... [-d 解到目录]
```

- 打包：`zip -r 包名.zip 目录`（`-r` 递归子目录）；
- 解包：`unzip 包名.zip`（默认解到当前目录）。

## 三、选项全表（对照 `zip --version` 与 `unzip -h`）

### 1. zip 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-r` | **递归**打包目录及子目录 | 压整个目录（最常用） |
| `-e` | 加密压缩（设密码） | 想给压缩包加密码 |
| `-0` | 只打包不压缩 | 内容已压缩过时 |
| `-9` | 最高压缩率 | 想要最小体积（较慢） |
| `-j` | 抛弃路径，只压文件本身 | 不要目录结构时 |
| `-d 条目` | 从 zip 里删除某个条目 | 事后删文件 |
| `-u` | 更新（只加变动过的） | 增量更新 |
| `-x 模式` | 排除匹配的文件 | 不压某些文件 |
| `-q` | 安静模式（不打印每个文件） | 脚本里 |

### 2. unzip 常用选项

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-l` | **列出**包内容（不解压） | 先看里面有啥（最常用） |
| `-d 目录` | 解到指定目录 | 解到别处（最常用） |
| `-o` | 覆盖已存在文件，不询问 | 脚本里强制覆盖 |
| `-n` | 已存在则跳过，不覆盖 | 避免覆盖 |
| `-t` | 测试压缩包完整性 | 检查包有没有坏 |
| `-v` | 详细列出内容 | 看大小/权限 |
| `-x 文件` | 解压时排除某些文件 | 不解某个文件 |
| `-p` | 解压到标准输出（管道） | 配合管道 |
| `-q` | 安静模式 | 不打印解压过程 |
| `-j` | 抛弃目录结构，文件全堆一起 | 不要路径时 |

## 四、由浅入深的典型示例

演示目录 `zipdemo/`：含 `a.txt`、`b.txt`、`dir/c.txt`。

### 示例 1：递归打包一个目录（最常用）

```bash
zip -r zipdemo.zip zipdemo
```

```text
  adding: zipdemo/ (stored 0%)
  adding: zipdemo/b.txt (stored 0%)
  adding: zipdemo/a.txt (stored 0%)
  adding: zipdemo/dir/ (stored 0%)
  adding: zipdemo/dir/c.txt (stored 0%)
```

> `-r` 是关键：不加 `-r` 只会打包目录本身（空壳），不进子目录。

### 示例 2：不解压，先看包里有什么

```bash
unzip -l zipdemo.zip
```

```text
Archive:  zipdemo.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        0  2026-09-30 23:28   zipdemo/
        2  2026-09-30 23:28   zipdemo/b.txt
        2  2026-09-30 23:28   zipdemo/a.txt
        0  2026-09-30 23:28   zipdemo/dir/
        2  2026-09-30 23:28   zipdemo/dir/c.txt
---------                     -------
        6                     5 files
```

> 解压前先 `-l` 看，防止解出一堆不想要的文件或路径。

### 示例 3：解包到当前目录

```bash
unzip zipdemo.zip
```

> 默认解到当前目录；如果文件已存在会询问是否覆盖。

### 示例 4：解包到指定目录

```bash
mkdir zout
unzip -q zipdemo.zip -d zout
find zout
```

```text
zout
zout/zipdemo
zout/zipdemo/b.txt
zout/zipdemo/a.txt
zout/zipdemo/dir
zout/zipdemo/dir/c.txt
```

> `-d zout` 解到 `zout/`，`-q` 安静模式。解包前先建目录，避免污染当前目录。

### 示例 5：强制覆盖不询问

```bash
unzip -o zipdemo.zip -d zout
```

> `-o` 覆盖已存在文件且不提示，脚本里常用。

### 示例 6：测试压缩包是否完好

```bash
unzip -t zipdemo.zip
```

> 逐个 CRC 校验，输出 "No errors detected" 说明包没坏。

### 示例 7：打包时排除某些文件

```bash
zip -r site.zip mysite -x "*.log" "*.git*"
```

> `-x` 排除日志和 git 目录。

### 示例 8：给压缩包加密码

```bash
zip -e secret.zip private_dir
```

> 会交互式输入两次密码；Windows 的资源管理器也能输密码解开。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `zip -r 包.zip 目录` | 递归打包（**最常用**） |
| `unzip -l 包.zip` | 列出包内容 |
| `unzip 包.zip` | 解到当前目录 |
| `unzip 包.zip -d 目录` | 解到指定目录 |
| `unzip -o 包.zip -d 目录` | 强制覆盖解包 |
| `unzip -t 包.zip` | 测试完整性 |
| `zip -r 包.zip 目录 -x "*.log"` | 打包并排除 |

## 六、RHEL 系与 Debian 系差异

`zip`/`unzip` 都是 Info-ZIP，**两系用法完全一致**。细微差别：

- 两系默认都可能不预装 `zip`/`unzip`，Debian 需 `apt install zip unzip`，RHEL 需 `dnf install zip unzip`；
- 中文文件名在旧版 unzip 可能乱码，可加 `-O CP936`（指定编码）解 Windows 压的中文包。

## 七、新手易错点

1. **打包忘了 `-r`**：只会压空目录壳，子目录里的文件没进去。
2. **解包前不 `-l` 看**：可能解出一堆散装文件污染当前目录；先 `-l`、再 `-d 目录`。
3. **中文文件名乱码**：Windows 压的 zip 在 Linux 解可能乱码，用 `unzip -O CP936 包.zip` 指定编码。
4. **`zip` 没有"解包"动作**：解包必须用 `unzip`，别拿 `zip` 去解。
5. **加密 zip 的 `-e` 要交互输密码**：脚本里不方便，可用其他工具。
6. **大目录 zip 比 tar.gz 慢且大**：追求压缩率和速度，服务器内部备份用 `tar -czf`；给 Windows 用户交付才用 `zip`。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands#压缩与打包)
- 服务器内部打包：`tar`（详解见 [tar](./tar)）
- 找大目录：`du`（详解见 [du](./du)）
- 文件系统：见 [Linux 文件系统专题](../../guide/linux-filesystem)
