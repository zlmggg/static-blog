# 解决SWAP报警提示

## 现象

初次安装Docker后，检查docker info，提示swap相关报错。

```bash
WARNING: No swap limit support
```

## 解决步骤

### 1. 检查swap配置

```bash
docker info
......
WARNING: No swap limit support

```

### 2. 配置swap `vim /etc/default/grub`

```bash
GRUB_DEFAULT=0
GRUB_TIMEOUT_STYLE=hidden
GRUB_TIMEOUT=2
GRUB_DISTRIBUTOR=`lsb_ release -i -s 2> /dev/null || echo Debian`
GRUB_CMDLINE_LINUX_DEFAULT=""
GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0 swapaccount=1"  #修改此行
```
### 3. 重启系统

重启系统后，检查swap配置是否生效。

```bash
update-grub
sudo reboot
```