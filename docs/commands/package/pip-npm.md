---
title: "pip / npm · 语言级包管理"
description: "pip 装 Python 包与虚拟环境、npm 装 Node 包与脚本、换国内镜像源、锁版本 requirements/package-lock。参数中文分级。"
---

# pip / npm · 语言级包管理

> 命令手册 · [软件包管理](/commands/package/) ｜ 频率：偶尔用
> 系统包管 OS 软件，pip/npm 管语言生态的库。Python 用 pip，Node.js 用 npm。

## 一句话用途

装 Python/Node 的第三方库，配镜像源加速，锁版本保证可复现。

## 高频场景速查

```bash
# pip（Python）
python -m pip install requests           # 装包
python -m pip install -r requirements.txt # 按清单装
python -m pip list                       # 已装列表
python -m pip freeze > requirements.txt  # 导出当前版本
python -m venv .venv && source .venv/bin/activate   # 虚拟环境

# npm（Node）
npm install                              # 按 package.json 装
npm install express                      # 装包并写入依赖
npm ci                                   # 按 lock 精确装（CI 用）
npm run build                            # 跑脚本
npm ls                                   # 依赖树
```

## 参数详解

### pip

| 参数 | 含义 |
|---|---|
| `install -r` | 按 requirements 装 |
| `install -i 镜像` | 指定源 |
| `freeze` | 导出精确版本 |
| `--user` | 装到用户目录（无 root） |
| `venv` | 建隔离虚拟环境 |

### npm

| 参数 | 含义 |
|---|---|
| `ci` | 按 package-lock 精确装（CI 推荐） |
| `install -D` | 装为开发依赖 |
| `install -g` | 全局装 |
| `--registry` | 指定源 |

## 运维实战

**换国内源加速**：

```bash
python -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
npm config set registry https://registry.npmmirror.com
```

**隔离环境**：Python 一定用 venv，别污染系统 Python（系统工具依赖它）。Node 项目用 `npm ci` 而非 `install` 保证 CI 与本地版本一致。

::: tip 易错点
`pip install` 直接装系统 Python 可能破坏 OS 工具（RHEL 的 yum 依赖系统 Python），务必用 venv。`npm install` 会改 lock，CI 用 `npm ci` 严格按 lock 装。
:::

## 相关命令

[dnf/yum](./dnf-yum) · [apt](./apt) · [make/gcc](./make-gcc)

## 官方文档

- pip：<https://pip.pypa.io/en/stable/>
- venv：<https://docs.python.org/3/library/venv.html>
- npm：<https://docs.npmjs.com/cli/v10/commands/npm>