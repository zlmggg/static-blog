---
category: 自动化
difficulty: 中级
---

# Git / GitLab / Jenkins 持续集成实战

::: tip 本篇定位
掌握版本控制 Git、私有代码托管 GitLab，并用 Jenkins 实现从代码提交到自动构建、打包、部署的持续集成（CI/CD）。本篇版本：GitLab CE 19.4.1、Jenkins LTS 2.568.3。
:::

## 一、Git 版本控制

### 1.1 Git 是什么

Git 是分布式版本控制系统，记录文件的修改历史，支持回退、分支、多人协作。与集中式版本库不同，每个开发者本地都有完整的版本库，可离线提交，再与远程同步。

### 1.2 三个工作区域

Git 文件在三个区域间流转，这是理解所有 Git 命令的基础：

- **工作区（Working Directory）**：你实际看到、正在编辑的文件；
- **暂存区（Stage/Index）**：`git add` 后、改动被临时存放的地方，对应 `.git/index`；
- **版本库（Repository）**：`git commit` 后，暂存区的改动被永久记录到版本库，对应 `.git` 目录。

![Git 三区流转：工作区经 git add 到暂存区，再经 git commit 到版本库，版本库经 push 到远程，远程经 pull 或 clone 回到工作区](/diagrams/jenkins-01.svg)

### 1.3 初始配置与建库

安装并配置提交者信息（每次提交都会记录，Windows 提交前必须先配置）：

```bash
apt install -y git
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
git config --global init.defaultBranch main   # 新仓库默认分支用 main
git config --global --list                     # 查看全局配置
```

配置作用域：`--global` 对当前用户生效（保存在 `~/.gitconfig`），`--system` 对所有用户（`/etc/gitconfig`），默认 `--local` 只对当前仓库（`.git/config`）。

在现有目录建库，或克隆远程库：

```bash
git init                 # 当前目录初始化为 Git 仓库
git init --bare repo.git # 裸仓库（无工作区），专门充当远程仓库
git clone <仓库URL>      # 克隆远程仓库到本地
```

### 1.4 日常命令

```bash
git status               # 查看当前状态（哪些改动未提交）
git add <文件>           # 添加到暂存区（. 表示全部）
git commit -m "说明"     # 提交到版本库
git diff                 # 工作区 vs 暂存区
git diff --staged        # 暂存区 vs 上次提交
git log --oneline --graph # 查看提交历史
git checkout -- <文件>   # 丢弃工作区改动（危险，不可恢复）
git restore <文件>       # 同上，新版写法
git reset --soft HEAD~1  # 撤销上次 commit（保留改动到暂存区）
git rm <文件>            # 同时从工作区和版本库删除
git mv 旧名 新名          # 改名
git stash                # 暂存当前未提交的改动，之后可恢复
```

### 1.5 分支管理

分支让你在不影响主线的情况下并行开发：

```bash
git branch               # 列出本地分支
git branch <分支名>       # 创建分支
git switch <分支名>       # 切换分支（新版，旧写法 checkout）
git switch -c <分支名>    # 创建并切换
git merge <分支名>        # 把指定分支合并到当前分支
git branch -d <分支名>    # 删除已合并的分支
git branch -r            # 列出远程分支
```

经典的 **GitFlow** 分支模型用几类固定分支管理发布：`master`（生产）、`develop`（开发主线）、`feature/*`（功能分支，从 develop 拉出再合回）、`release/*`（发布准备，合回 master 和 develop）、`hotfix/*`（生产紧急修复，从 master 拉出、修复后合回 master 和 develop）。小团队也常采用更简单的主干开发。

### 1.6 远程协作

```bash
git remote -v                       # 查看远程仓库
git remote add origin <URL>         # 关联远程仓库
git push -u origin main             # 首次推送并建立跟踪
git push origin <分支>              # 推送分支
git push origin --tags              # 推送标签
git fetch origin                    # 拉取远程更新但不自动合并
git pull origin main                # 拉取并合并（= fetch + merge）
```

`.gitignore` 文件用来声明不纳入版本库的文件（如 `node_modules/`、`*.log`、密钥文件）。

## 二、GitLab 私有代码托管

### 2.1 GitLab 与 Omnibus

GitLab 是基于 Web 的 Git 仓库管理平台，提供代码托管、评审、Issue、CI/CD 等功能。它组件众多（Web、后台任务、PostgreSQL、Redis、Gitaly 等），官方通过 **Omnibus GitLab** 安装包把所有组件打包在一起、用 Chef 自动编排，安装和升级都很方便。统一管理命令是 `gitlab-ctl`。

从 GitLab 12.1 起，官方 Linux 包只支持 PostgreSQL，不再支持 MySQL。

### 2.2 硬件要求

GitLab 比较吃资源，官方建议生产内存 4 GB 以上、较新版本建议 8 GB 左右。小内存机器可用于实验但要加 swap、并调小并发。磁盘根据代码量和 CI 产物准备。

### 2.3 安装 GitLab CE 19.4.1

以 Ubuntu 24.04（noble）为例，从清华镜像下载 Omnibus 包：

```bash
apt update && apt install -y curl openssh-server ca-certificates perl
cd /root
wget https://mirrors.tuna.tsinghua.edu.cn/gitlab-ce/ubuntu/pool/noble/main/g/gitlab-ce/gitlab-ce_19.4.1-ce.0_amd64.deb
apt install ./gitlab-ce_19.4.1-ce.0_amd64.deb -y
```

::: tip 版本号与镜像目录
上面是 19.4.1 的标准包名（`gitlab-ce_<版本>-ce.0_amd64.deb`）。若镜像里小版本已更新，可到 https://mirrors.tuna.tsinghua.edu.cn/gitlab-ce/ubuntu/pool/noble/main/g/gitlab-ce/ 目录里选需要的版本。RHEL/Rocky 用对应 yum 镜像目录下的 rpm 包，安装方式一致。
:::

### 2.4 配置并初始化

编辑主配置文件 `/etc/gitlab/gitlab.rb`，设置访问地址（可用域名或 IP）：

```ruby
external_url 'http://gitlab.example.com'
# 可选：直接指定 root 初始密码（不指定则随机生成）
gitlab_rails['initial_root_password'] = '你的强密码'
```

执行重新配置，让 Omnibus 按配置初始化并启动所有服务（首次较慢）：

```bash
gitlab-ctl reconfigure
gitlab-ctl status
```

若没有在配置里指定 root 密码，随机密码保存在 `/etc/gitlab/initial_root_password`（该文件在首次 reconfigure 后约 24 小时自动删除，请及时查看保存）。

::: tip 常用命令
`gitlab-ctl reconfigure`（改完 gitlab.rb 后执行）、`gitlab-ctl restart|status`、`gitlab-ctl tail`（看日志）。改 external_url 后必须重新 reconfigure。
:::

### 2.5 用户、组、项目与角色

- **用户**：管理员在管理区创建用户（邮箱不能重复），创建后可编辑用户、设置初始密码；
- **组（Group）**：一个组里可放多个项目，把开发者加入组并赋予角色，便于按团队批量管理；
- **项目（Project）**：代码仓库归属于个人或组，可选择初始化 README；
- **权限角色（组内 5 级）**：

| 角色 | 主要权限 |
|---|---|
| Guest | 只能提 Issue、发评论，不能读写代码库 |
| Reporter | 能克隆/查看代码，不能提交（适合 QA、产品） |
| Developer | 能克隆、开发、提交、推送非保护分支（普通开发） |
| Maintainer | 能管理项目、保护分支、合并到主干 |
| Owner | 组/项目最高权限，可改设置、管理成员 |

本地通过 HTTP 或 SSH 推拉代码，SSH 方式需在用户"个人设置 → SSH 密钥"里添加本机公钥。

## 三、Jenkins 安装

### 3.1 安装 Java

Jenkins LTS 2.568.3 需要 **Java 17 或 21**（Java 必须先于 Jenkins 安装；若后装 Java 需要重启系统）：

```bash
apt update
apt install -y openjdk-21-jdk
java -version
```

### 3.2 添加 Jenkins 仓库并安装

以 Ubuntu 为例，使用清华镜像的 LTS 仓库（比官方源快）：

```bash
# 添加 Jenkins 仓库密钥
wget -q -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key

# 添加清华 LTS 软件源
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://mirrors.tuna.tsinghua.edu.cn/jenkins/debian-stable binary/" \
  > /etc/apt/sources.list.d/jenkins.list

apt update
apt install -y jenkins
systemctl enable --now jenkins
ss -tnlp | grep 8080
```

::: tip 也可以直接下载 deb
在 https://mirrors.tuna.tsinghua.edu.cn/jenkins/debian-stable/ 下载对应版本（如 jenkins_2.568.3_all.deb），用 `apt install ./jenkins_2.568.3_all.deb` 安装，效果相同。RHEL/Rocky 用对应 yum 源或 rpm。
:::

### 3.3 初始化向导

浏览器访问 `http://服务器IP:8080`：

1. 查看初始管理员密码：

```bash
cat /var/lib/jenkins/secrets/initialAdminPassword
```

2. 粘贴密码进入；
3. 选择"安装推荐插件"（Install suggested plugins），等待安装；
4. 创建第一个管理员用户并保存；
5. 实例配置保持默认，进入 Jenkins 主界面。

### 3.4 中文界面

在 **Manage Jenkins → Plugins（插件管理）** 搜索安装 `Localization: Chinese (Simplified)`，安装后重启即可显示中文；若部分仍为英文，可配合 `Locale` 插件在全局设置里把默认语言设为 `zh_CN`。

## 四、自由风格任务

自由风格（Freestyle）项目通过界面配置一个构建任务，适合入门理解 CI 的各个环节。

### 4.1 准备构建环境（JDK / Maven）

Java 项目需要构建工具，常用 Maven。两种方式：

- **自动安装（推荐新手）**：在 **Manage Jenkins → Tools（全局工具配置）** 里配置 JDK、Maven，勾选自动安装，Jenkins 会在首次构建时自动下载；
- **手动安装**：在服务器上装好并配置 Maven，国内建议改 Maven 镜像加速（编辑 `/etc/maven/settings.xml`，mirror 指向阿里云 Maven 源）。

### 4.2 配置凭据

在 **Manage Jenkins → Credentials（凭据）** 添加，常用两类：

- **用户名/密码**：用于拉取 GitLab 私有仓库（填 GitLab 账号密码或访问令牌）；
- **SSH 密钥**：用于 Jenkins 免密登录目标部署机。可在服务器上以 jenkins 用户生成密钥并把公钥拷到目标机：

```bash
su - jenkins
ssh-keygen
ssh-copy-id root@目标机IP
```

### 4.3 创建自由风格项目

新建 Item 选 Freestyle project，按构建环节配置：

1. **源码管理**：选 Git，填仓库 URL，选择凭据，指定分支（如 `*/main`）；
2. **构建触发器**：可先选手动，后续用 webhook（见第六节）；
3. **构建步骤**：如调用 Maven 执行 `clean package -Dmaven.test.skip=true` 打成 jar/war；
4. **构建后操作**：通过 "Publish over SSH" 或在构建步骤里用 SSH 把产物传到目标机、执行部署脚本（停旧进程、替换包、启动新进程）；
5. 可加 **邮件通知（E-mail Notification）**，构建失败时发送。

### 4.4 构建脚本思路

部署脚本通常包含：备份旧版本 → 停止旧服务 → 替换新包 → 启动服务 → 健康检查。把脚本放在目标机，由 Jenkins 通过 SSH 调用，比把大量命令堆在 Jenkins 界面更清晰可复用。

## 五、Pipeline 流水线

### 5.1 声明式 Pipeline

Pipeline 用代码（Jenkinsfile）描述整个交付流程，可版本化、可可视化、可分阶段，是 Jenkins 的主流用法。声明式基本结构：

```groovy
pipeline {
  agent any
  tools {
    jdk 'jdk-21'
    maven 'maven-3.9'
  }
  environment {
    IMAGE = "registry.example.com/demo/myapp"
    TAG   = "${BUILD_NUMBER}"
  }
  stages {
    stage('拉取代码') {
      steps {
        git branch: 'main', credentialsId: 'gitlab-cred', url: 'http://gitlab.example.com/devops/myapp.git'
      }
    }
    stage('测试') {
      steps { sh 'mvn clean test' }
    }
    stage('打包') {
      steps { sh 'mvn -Dmaven.test.skip=true clean package' }
    }
    stage('构建镜像') {
      steps { sh 'docker build -t ${IMAGE}:${TAG} .' }
    }
    stage('推送镜像') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'registry-cred',
          usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
          sh 'docker login -u ${REG_USER} -p ${REG_PASS} registry.example.com'
          sh 'docker push ${IMAGE}:${TAG}'
        }
      }
    }
    stage('部署') {
      steps {
        sh 'ssh root@目标机 "docker rm -f myapp; docker run -d --name myapp -p 80:8080 ${IMAGE}:${TAG}"'
      }
    }
  }
  post {
    success { echo '流水线成功' }
    failure { echo '流水线失败，请检查' }
  }
}
```

### 5.2 Jenkinsfile 放哪里

- 新建 Pipeline 任务，在 Pipeline 定义里选 "Pipeline script from SCM"，指向代码库里的 `Jenkinsfile`，这样流水线和代码一起版本管理（推荐）；
- 也可直接在任务里写 Pipeline script 做快速测试。

### 5.3 阶段视图

Pipeline 运行后，Jenkins 会展示各阶段（Stage View），每个阶段成功/失败一目了然，失败时可从失败的阶段定位问题并重试。

## 六、实战：提交代码自动构建部署

把上面环节串起来，实现"开发者 push 代码 → Jenkins 自动构建部署"：

![CI/CD 全流程：开发者 push 到 GitLab，GitLab 经 Webhook 通知 Jenkins，Jenkins 拉取代码后依次编译测试、打包构建镜像、推送制品，再 SSH 部署到目标机并通知结果](/diagrams/jenkins-02.svg)

配置步骤：

1. Jenkins 安装 **GitLab 插件**（会带来 GitLab 触发器）；
2. 在 GitLab 管理区允许外发请求：**Admin Area → Settings → Network → Outbound requests**，勾选允许；
3. 在 Jenkins 自由风格/Pipeline 任务里开启 GitLab 触发器，生成并复制 Webhook URL 和 secret token；
4. 在 GitLab 对应项目的 **Settings → Webhooks** 里填入 Jenkins 的 URL，保存；
5. 用 "Test → Push events" 验证连通；
6. 之后修改代码并 `git commit && git push`，Jenkins 会自动触发整条流水线。

![声明式 Pipeline 各阶段：拉取代码、测试、打包、构建镜像、推送、部署依次进行](/diagrams/jenkins-03.svg)

## 面试自测

1. Git 是集中式还是分布式？分布式体现在哪里？
2. 说清 Git 的工作区、暂存区、版本库，以及 add、commit、push 分别在哪些区域间流转。
3. git config 的 global/system/local 作用域分别保存在哪里？
4. git reset、git restore、git checkout 在撤销改动时有什么区别和风险？
5. git stash 有什么用？
6. 描述 GitFlow 分支模型中 master、develop、feature、release、hotfix 的关系。
7. git fetch 和 git pull 有什么区别？
8. .gitignore 的作用？
9. GitLab 的 Omnibus 安装方式解决了什么问题？统一管理命令是什么？
10. GitLab 为什么只支持 PostgreSQL？
11. GitLab 安装后 root 初始密码在哪里？为什么要尽快保存？
12. 改了 external_url 之后为什么要执行 reconfigure？
13. GitLab 的 Guest、Reporter、Developer、Maintainer、Owner 权限有什么区别？
14. Jenkins 对 Java 版本有什么要求？Java 应该什么时候装？
15. Jenkins 初始管理员密码在哪个文件？首次访问要做哪些初始化？
16. Jenkins 凭据里用户名密码和 SSH 密钥分别用于什么场景？
17. 自由风格任务从源码到部署一般配置哪几个环节？
18. 什么是声明式 Pipeline？相比自由风格有什么优势？
19. Jenkinsfile 为什么推荐放在代码库、从 SCM 读取？
20. Pipeline 的 post 块能做什么？
21. 如何实现"push 代码自动触发 Jenkins 构建"？GitLab 端要开启什么？
22. 简述 CI/CD 的含义，以及一条流水线通常包含哪些阶段。

## 相关速查

- 命令速查：[Linux 命令速查](/reference/linux-commands)、[Docker 命令速查](/reference/docker-commands)、[kubectl 命令速查](/reference/kubectl-commands)
- 官方资源：
  - Git 官方文档：https://git-scm.com/doc
  - Git 常用命令（中文手册）：https://git-scm.com/book/zh/v2
  - GitLab 官网：https://about.gitlab.com/
  - GitLab 官方文档：https://docs.gitlab.com/
  - Omnibus GitLab：https://gitlab.com/gitlab-org/omnibus-gitlab
  - GitLab CE 清华镜像：https://mirrors.tuna.tsinghua.edu.cn/gitlab-ce/
  - Jenkins 官网：https://www.jenkins.io/
  - Jenkins 用户文档：https://www.jenkins.io/doc/
  - Jenkins LTS 更新日志：https://www.jenkins.io/changelog-stable/
  - Jenkins 清华镜像：https://mirrors.tuna.tsinghua.edu.cn/jenkins/
  - Pipeline 语法参考：https://www.jenkins.io/doc/book/pipeline/syntax/
  - 阿里云 Maven 镜像：https://developer.aliyun.com/mvn/guide

