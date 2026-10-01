---
category: Linux
difficulty: 中级
date: 2020-05-22
---

# 异常掉电后文件系统损坏，fsck 修复与只读挂载（2020-05-22）

## 现象

机房突然断电，服务器重启后卡在启动界面，最后进入 emergency mode：

```
You are in emergency mode. After logging in, type "journalctl -xb" to view logs,
"systemctl reboot" to reboot, "systemctl default" or "exit" to boot into default mode.
Give root password for maintenance
(or press Control-D to continue):
```

登录后看到根分区被只读挂载了：

```
mount | grep " / "
# /dev/sda2 on / type ext4 (ro,relatime)
```

写任何文件都报 `Read-only file system`。`dmesg` 里大量 ext4 错误：

```
EXT4-fs error (device sda2): ext4_lookup: inode #12345: comm systemd: deleted inode
EXT4-fs error (device sda2): ext4_find_entry: checking inode #12345
Remounting filesystem read-only
```

## 环境

- 发行版：Ubuntu 18.04.4 LTS
- 内核：`4.15.0-99-generic`
- 文件系统：ext4（根分区 `/dev/sda2`）
- 故障原因：机房 UPS 故障，硬断电

## 定位过程

### 1. 先看 dmesg / journal 确认是哪个文件系统坏了

```bash
dmesg -T | grep -i "ext4\|xfs\|error\|remount"
journalctl -xb | grep -i "fsck\|emergency"
```

日志里明确指向 `/dev/sda2` 上的 ext4 出现元数据不一致，内核为了保护数据自动把它 remount 成只读。

### 2. 确认分区当前状态

```bash
mount | grep sda2
# /dev/sda2 on / type ext4 (ro,relatime,data=ordered)

cat /proc/mounts | grep sda2
```

### 3. 不要急着 mount -o remount,rw

文件系统元数据已经不一致，强行 rw 挂载会扩大损坏。必须先 fsck。

## 解决步骤

### 1. 临时止血：如果是别的分区坏了，先把根分区搞正常

根分区坏了没法在系统里 fsck 自己，需要用 Live CD / 安装 U 盘救援模式启动。
如果坏的是数据分区（如 `/data`），可以直接在系统里操作：

```bash
# 先卸载坏分区
umount /data

# 先检查不修复（看坏到什么程度）
e2fsck -n /dev/sda3

# 确认后再修复（-y 自动回答 yes）
e2fsck -y /dev/sda3
```

### 2. 根分区坏了：用 U 盘救援

1. 用 Ubuntu 18.04 安装 U 盘启动，选 Try Ubuntu。
2. 找到根分区设备：

```bash
lsblk
# sda2 是根分区
```

3. 执行 fsck：

```bash
e2fsck -y /dev/sda2
```

`e2fsck` 可能会问很多次 yes，`-y` 全部自动同意。过程中如果提示 "Clear inode?"、"Fix? " 都选 yes。
修复完会提示 `***** FILE SYSTEM WAS MODIFIED *****`。

4. 重启拔 U 盘：

```bash
reboot
```

### 3. 启动后确认

```bash
mount | grep " / "
# /dev/sda2 on / type ext4 (rw,relatime,data=ordered)
# 应该是 rw 了

touch /tmp/testfile && echo OK
```

### 4. 如果是 XFS 文件系统

XFS 不能用 e2fsck，要用 `xfs_repair`：

```bash
umount /data
xfs_repair /dev/sda3
# 如果日志损坏严重，先清日志：
xfs_repair -L /dev/sda3   # -L 会丢日志里未提交的数据
```

## 验证与预防

- 修复后 `dmesg | grep -i ext4` 不再有新错误。
- 跑一次 `smartctl -a /dev/sda` 看硬盘有没有坏道，断电后磁盘容易出硬件问题。
- 重要服务器一定要配 UPS，不要硬断电。
- fstab 里加 `errors=remount-ro`（ext4 默认就是），让文件系统出问题时只读而不是直接宕机。
- 定期做磁盘 SMART 巡检，提前发现硬盘老化。

## 相关

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 启动方向：[GRUB 损坏启动失败](/cases/t-grub-rescue-boot)
- 磁盘方向：[磁盘空间写满](/cases/t-disk-space-full)
- 巡检清单：[运维巡检清单](/reference/ops-checklists)
