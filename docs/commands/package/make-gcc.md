---
title: "make / gcc · 源码编译"
description: "源码编译三步（configure/make/make install）、gcc 常用参数、make 并行与指定路径、编译依赖处理。缺包或定制版本时用。"
---

# make / gcc · 源码编译

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：很少用
> 仓库没有想要的版本、或要定制编译选项时，从源码编译。日常优先用包管理器，编译是兜底。

## 一句话用途

把源码变成可执行程序：configure 探测环境 → make 编译 → make install 安装。

## 高频场景速查

```bash
# 经典三步
tar xf nginx-1.27.tar.gz && cd nginx-1.27
./configure --prefix=/usr/local/nginx --with-http_ssl_module
make -j$(nproc)                      # 并行编译，快
sudo make install

# gcc 直接编译
gcc -O2 -o hello hello.c             # 编译优化
gcc -Wall -g -o app app.c            # 开警告+调试信息
```

## 参数详解

### make

| 参数 | 含义 |
|---|---|
| `-jN` | N 个并行任务（常 `$(nproc)`） |
| `-C dir` | 切到 dir 执行 |
| `make install` | 安装到 prefix |
| `make clean` | 清编译产物 |

### gcc

| 参数 | 含义 |
|---|---|
| `-o` | 输出文件名 |
| `-O2` | 优化级别 |
| `-Wall` | 开全部警告 |
| `-g` | 带调试信息（gdb 用） |
| `-I` / `-L` / `-l` | 头文件目录 / 库目录 / 链接库 |
| `-shared -fPIC` | 编共享库 .so |

## 运维实战

**编译报缺头文件**：`configure: error: ... headers not found` → 装对应 -devel/-dev 包（如 openssl-devel、pcre-devel）。先 `dnf groupinstall "Development Tools"` 装齐 gcc/make。

**指定安装路径**：`--prefix=/usr/local/xxx` 装到独立目录，不污染系统包管理，卸载直接删目录。

::: tip 易错点
源码编译装的软件**不受包管理器管理**，升级/卸载要手动。生产能用包就用包，编译只为定制或缺包。`make -j` 并行数别超内存承受（大项目易 OOM）。
:::

## 相关命令

[dnf/yum](./dnf-yum) · [ldconfig](./ldconfig) 动态库 · [repoquery](./repoquery-apt-file) 查编译依赖

## 官方文档

- GCC：<https://gcc.gnu.org/onlinedocs/>
- GNU Make：<https://www.gnu.org/software/make/manual/>