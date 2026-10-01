# mv 命令详解：移动和重命名文件

> 本文是 [Linux 命令速查](../linux-commands#文件与目录) 中 `mv` 的从 0 到 1 详解。
> 目标：把 `mv --help` 里的每个选项讲清楚，多看几遍后，你在服务器上敲 `mv --help` 就知道该用哪个选项。
> 环境依据：GNU coreutils 8.32（Ubuntu 22.04 自带；RHEL/Rocky 自带版本用法一致）。

## 一、命令是干什么的

`mv` 是 **move（移动）** 的缩写，一件事干两种活：

1. **重命名**：`mv old.txt new.txt`——同一目录下改名；
2. **移动**：`mv file.txt 别的目录/`——把文件搬到另一个地方。

它和 `cp` 的区别：`cp` 复制后源文件还在；`mv` 是把源文件**拿走**，原位置不再保留。

> 类比：Windows 里"剪切 + 粘贴"就是 `mv`，"重命名"也是 `mv`（在同一个文件夹里剪切粘贴，路径不变只改名字）。

属于 GNU coreutils。

## 二、命令语法

```bash
mv [选项]... [-T] 源 目标
mv [选项]... 源... 目录          # 多个源一起移进目录
mv [选项]... -t 目录 源...
```

- `源`：要移动/改名的文件或目录；
- `目标`：在同目录下就是"新名字"，在不同目录下就是"搬过去的目的地"；
- 移动目录**不需要 `-r`**（和 `cp` 不同！），`mv` 天生就能搬目录。

最简单的用法：

```bash
mv old.txt new.txt
```

## 三、选项全表（对照 `mv --help`）

### 1. 控制"覆盖前怎么办"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-i`，`--interactive` | 覆盖前**询问** | 怕误覆盖时 |
| `-n`，`--no-clobber` | **不覆盖**已存在的目标 | 安全移动，绝不顶掉旧文件 |
| `-f`，`--force` | **不询问**直接覆盖（默认行为） | 确定要覆盖时 |

> 这三个若同时给，**最后一个生效**。不带任何选项时 `mv` 默认就是"直接覆盖不提问"。

### 2. 控制"何时才移动"

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-u`，`--update` | **只在源比目标新、或目标不存在时**才覆盖移动 | 增量更新 |

### 3. 目标位置与备份

| 选项 | 中文含义 | 什么场景用 |
|---|---|---|
| `-t 目录`，`--target-directory=目录` | 把后面所有源移进该目录 | 一次移多个文件到一处 |
| `-T`，`--no-target-directory` | 把目标当普通文件，不当目录 | 防止目标是目录时被误塞进去 |
| `--backup[=CONTROL]` | 覆盖前给旧目标做备份 | 怕覆盖坏时 |
| `-b` | 同 `--backup`，不带参数 | 简单备份 |
| `-S 后缀`，`--suffix=SUFFIX` | 改备份后缀（默认 `~`） | 自定义备份名 |
| `--strip-trailing-slashes` | 去掉源末尾的 `/` | 路径规范处理 |
| `-v`，`--verbose` | 打印每个移动动作 | 看它移了什么 |
| `-Z`，`--context` | 设目标的 SELinux 上下文 | RHEL 开 SELinux 时 |

## 四、由浅入深的典型示例

### 示例 1：重命名

```bash
echo "data" > old.txt
mv old.txt new.txt
ls
```

```text
new.txt
```

> 同目录下 `mv` 就是改名：`old.txt` 变成了 `new.txt`。

### 示例 2：移动到另一个目录

```bash
mkdir backup
mv new.txt backup/
ls backup
```

```text
new.txt
```

> `new.txt` 被搬进了 `backup/` 里。

### 示例 3：移动同时改名（一步到位）

```bash
mv backup/new.txt restored.txt
ls
```

```text
backup
restored.txt
```

> 既搬走、又改名，一条命令搞定。

### 示例 4：-i 覆盖前询问

```bash
echo v1 > a.txt; echo v2 > b.txt
echo "n" | mv -i b.txt a.txt
cat a.txt
```

```text
mv: overwrite 'a.txt'? a.txt = v1
```

> 它问"覆盖 a.txt 吗"，我们答 `n`（不），所以 `a.txt` 还是 v1。

### 示例 5：-n 绝不覆盖

```bash
mv -n b.txt a.txt
cat a.txt
```

```text
v1
```

> `a.txt` 已存在，`-n` 让它直接跳过，`b.txt` 都还在原地。

### 示例 6：-v 打印动作

```bash
mkdir d1
mv -v restored.txt d1/
```

```text
renamed 'restored.txt' -> 'd1/restored.txt'
```

### 示例 7：-u 只在源更新时才覆盖

```bash
touch d1/restored.txt      # 让目标变新
echo fresh > newer.txt
mv -v -u newer.txt d1/restored.txt && echo "发生了移动"
```

```text
renamed 'newer.txt' -> 'd1/restored.txt'
发生了移动
```

> 这里源 `newer.txt` 比目标新，所以覆盖成功；反过来如果目标更新，它就什么都不做。

## 五、高频组合速记

| 命令 | 用途 |
|---|---|
| `mv old new` | 重命名（**最常用**） |
| `mv 文件 目录/` | 移动文件到目录 |
| `mv -i 文件 目录/` | 覆盖前询问（安全） |
| `mv -n 文件 目录/` | 绝不覆盖 |
| `mv -v ...` | 看移动了什么 |
| `mv *.log logs/` | 把所有日志移进 logs 目录 |

## 六、RHEL 系与 Debian 系差异

`mv` 属于 GNU coreutils，**两系用法完全一致**。细微差别：

- 很多发行版把 `mv` 别名成 `mv -i`（覆盖前询问）；脚本里想无人值守移动，请显式加 `-f` 或 `-n`，别依赖别名；
- 跨文件系统移动大文件时，`mv` 实际是"复制+删除"，速度比同盘改名慢，属正常。

## 七、新手易错点

1. **`mv` 覆盖没有回收站**：目标已存在会被直接顶掉，**不可恢复**；重要操作先 `-i` 或 `-n`。
2. **移动目录不用 `-r`**：这和 `cp` 不一样，`mv 目录 别处/` 直接就能搬，别多此一举加 `-r`。
3. **目标目录末尾要不要 `/`**：`mv a.txt dir` 和 `mv a.txt dir/` 效果通常一样，但目标若不存在就会变成"改名"——拿不准先 `ls`。
4. **`mv` 不保留旧副本**：它是剪切不是复制；误移错地方就再 `mv` 回去。
5. **通配符移动要小心**：`mv *.log logs/` 会把当前目录所有 `.log` 都搬走，先 `ls *.log` 确认范围。
6. **跨盘移动大文件会慢**：同分区是瞬间改名，跨分区要真复制数据。

## 八、相关命令与文档

- 速查页：[Linux 命令速查](../linux-commands)
- 复制（保留源文件）：`cp`（详解见 [cp](./cp)）
- 删除：`rm`（详解见 [rm](./rm)）
- 看目录内容确认移动结果：`ls`（详解见 [ls](./ls)）
- Shell 通配符概念：见 [Shell 入门](../../guide/linux-shell)
