---
title: "ldconfig · 动态库缓存"
description: "ldconfig 刷新动态库缓存、ldd 查程序依赖的 .so、排「error while loading shared libraries」找不到库。参数中文分级。"
---

# ldconfig · 动态库缓存

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：很少用
> 程序启动报 `error while loading shared libraries: libxxx.so: cannot open` 时，多半是动态库没被找到，用 ldconfig/ldd 排。

## 一句话用途

让系统找到新装的共享库（.so），并查程序到底缺哪个库。

## 高频场景速查

```bash
ldd /usr/local/nginx/sbin/nginx      # 查程序依赖哪些 .so（not found=缺）
sudo ldconfig                        # 刷新动态库缓存
sudo ldconfig -p | grep ssl          # 查缓存里有没有某库
echo '/usr/local/lib' | sudo tee /etc/ld.so.conf.d/local.conf
sudo ldconfig                        # 加自定义库目录后刷新
```

## 参数详解

| 命令/参数 | 含义 |
|---|---|
| `ldconfig` | 重建 /etc/ld.so.cache 缓存 |
| `ldconfig -p` | 打印缓存里所有库 |
| `ldconfig -v` |  verbose 看扫描了哪些目录 |
| `ldd 程序` | 列程序依赖的库及解析路径 |
| `LD_LIBRARY_PATH` | 临时指定库搜索路径（环境变量） |

## 运维实战

**源码装了库但程序找不到**：库装到 /usr/local/lib，但系统默认只搜 /lib、/usr/lib。把该目录写进 `/etc/ld.so.conf.d/xxx.conf`，再 `sudo ldconfig` 刷新缓存。

**临时验证**：`LD_LIBRARY_PATH=/usr/local/lib ./app` 临时加搜索路径，确认是库路径问题后再持久化。

::: tip 易错点
`ldd` 对不可信程序有安全风险（可能触发执行），只对自己编译/可信程序用。新装库后**必须 ldconfig**，否则缓存不更新程序仍找不到。
:::

## 相关命令

[make/gcc](./make-gcc) 编译 · [repoquery](./repoquery-apt-file) 查库归属 · [strings](/commands/observe/) 看二进制

## 官方文档

- ldconfig：<https://man7.org/linux/man-pages/man8/ldconfig.8.html>
- ldd：<https://man7.org/linux/man-pages/man1/ldd.1.html>