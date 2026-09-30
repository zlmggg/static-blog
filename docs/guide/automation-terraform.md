# Terraform 基础设施即代码实战

::: tip 本篇定位
用 Terraform 以"基础设施即代码（IaC）"的方式，通过代码创建和管理云服务器、网络、数据库等资源。本篇版本：Terraform v1.16.4，以阿里云 Provider 为例。
:::

## 一、基础设施即代码（IaC）

### 1.1 什么是 IaC

基础设施即代码，是把服务器、网络、数据库等基础设施的定义，像应用代码一样用文件描述、纳入版本管理，并通过工具自动创建和变更。相比在控制台手工点击，它带来：

- **可重复**：同一份代码可快速复制出开发、测试、生产多套环境，配置一致；
- **可追溯**：基础设施的每次变更都有 Git 记录，可审查、可回滚；
- **高效**：一条 `terraform apply` 即可在分钟级完成复杂环境部署；
- **减少人为失误**：避免手工操作的遗漏和不一致。

### 1.2 Terraform 的定位

Terraform 是 HashiCorp 开源的基础设施**编排**工具，专注资源的创建、更新、销毁全生命周期，通过**状态文件（state）**追踪资源实际状态与代码期望状态的差异，并能跨云（阿里云、AWS、腾讯云等）统一编排。

它与配置管理工具（如 Ansible）侧重点不同：

| 对比 | Terraform | Ansible |
|---|---|---|
| 核心定位 | 基础设施资源编排（创建/销毁） | 软件配置与状态管理（装软件、改配置） |
| 状态管理 | 有独立 state 文件追踪差异 | 无状态，每次按清单执行 |
| 典型场景 | 建 VPC、开 ECS、建数据库 | 在已有机器上部署应用、维护配置 |

实际项目中两者常配合：Terraform 负责"把资源建出来"，Ansible 负责"在资源上做配置"。

### 1.3 工作原理

![Terraform 工作原理：CLI 同时读取 HCL 配置（期望状态）和 State（实际状态），计算差异后调用 Provider 插件，通过云平台 API 操作云资源](/diagrams/terraform-01.svg)

Terraform CLI 读取 HCL 配置（期望状态）和 state（实际状态），计算出差异后，调用对应云厂商的 Provider 插件，通过云 API 完成资源变更。

## 二、核心概念

### 2.1 Provider（提供者）

Provider 是 Terraform 与各类平台对接的插件，由云厂商或社区提供，封装了该平台的资源和 API，如阿里云 `alicloud`、AWS `aws`。在 `terraform { required_providers }` 中声明来源和版本，执行 `init` 时自动下载。

### 2.2 Resource（资源）

资源是 Terraform 最核心的概念，代表一个具体基础设施对象（一台 ECS、一个 VPC、一个安全组）。每个资源由**资源类型**和**资源名称**唯一标识，如 `alicloud_instance.web`。

```hcl
resource "alicloud_vpc" "myvpc" {
    vpc_name   = "the-first-vpc"
    cidr_block = "172.16.0.0/12"
}
```

- 块内参数必须缩进（官方推荐 2 个空格），不缩进会报语法错误；
- 资源通过引用其他资源属性形成**隐式依赖**，Terraform 据此自动确定创建顺序；也可用 `depends_on` 显式指定。

### 2.3 HCL 语法

HCL（HashiCorp Configuration Language）是 Terraform 的配置语言，用块（block）和键值参数描述资源，支持字符串、数字、列表（`[...]`）、对象、注释（`#`）。常用文件：`main.tf`（主配置）、`variables.tf`（变量定义）、`outputs.tf`（输出）。

### 2.4 Variable（变量）与 Output（输出）

变量让配置可参数化、避免硬编码：

```hcl
variable "region" {
  type    = string
  default = "cn-chengdu"
}
```

输出用于在 apply 后展示关键信息（如实例公网 IP）：

```hcl
output "public_ip" {
  value = alicloud_instance.web.public_ip
}
```

变量值可用 `-var`、`*.tfvars` 文件或环境变量传入；敏感信息（密码、密钥）不要写死在代码里。

## 三、安装 Terraform

### 3.1 下载二进制（简单、版本可控）

```bash
apt update && apt install -y wget unzip
cd /tmp
wget https://releases.hashicorp.com/terraform/1.16.4/terraform_1.16.4_linux_amd64.zip
unzip terraform_1.16.4_linux_amd64.zip
mv terraform /usr/local/bin/
terraform version
```

国内下载 HashiCorp 官方地址慢时，可使用加速代理，或通过系统包管理器（HashiCorp 官方 apt/yum 仓库）安装。

### 3.2 配置云账号认证

以阿里云为例，推荐用**环境变量**提供 AccessKey（不要把密钥写进 .tf 文件并提交）：

```bash
export ALICLOUD_ACCESS_KEY="你的AccessKeyId"
export ALICLOUD_SECRET_KEY="你的AccessKeySecret"
export ALICLOUD_REGION="cn-chengdu"
```

::: warning AccessKey 安全
为账号创建只授予所需权限的 RAM 子用户 AccessKey，遵循最小权限；不要用主账号 AK。代码仓库里若误提交密钥，应立即在云控制台禁用并轮换。
:::

## 四、核心工作流命令

| 命令 | 作用 |
|---|---|
| `terraform init` | 初始化工作目录，下载 Provider、初始化后端；可多次执行，无副作用 |
| `terraform validate` | 校验配置语法是否正确 |
| `terraform fmt` | 统一代码格式 |
| `terraform plan` | 对比期望状态与实际状态，预览将要增、改、删的资源，不真正执行 |
| `terraform apply` | 执行变更，创建/更新/删除资源，并更新 state |
| `terraform destroy` | 销毁由 Terraform 管理的全部资源 |

典型流程：写好配置 → `init` → `plan` 确认计划 → `apply` 执行。销毁也可先生成销毁计划 `terraform plan -destroy -out=tf.plan` 再执行，更可控。

## 五、阿里云 ECS 实战

目标：用代码创建一套包含 VPC、交换机、安全组、ECS 实例的最小环境。资源关系如下：

![阿里云资源拓扑：VPC 下包含交换机和安全组，ECS 实例位于交换机中并关联安全组，安全组入方向放行 SSH](/diagrams/terraform-02.svg)

### 5.1 变量文件 variables.tf

```hcl
variable "region" {
  type    = string
  default = "cn-chengdu"
}

variable "zone_id" {
  type    = string
  default = "cn-chengdu-l"
}

variable "instance_password" {
  type      = string
  sensitive = true
}
```

### 5.2 主配置 main.tf

```hcl
terraform {
  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.245"
    }
  }
}

provider "alicloud" {
  region = var.region
}

# 查询最新的 Ubuntu 24.04 镜像，避免硬编码 image_id
data "alicloud_images" "ubuntu" {
  name_regex  = "^ubuntu_24"
  most_recent = true
  owners      = "system"
}

# VPC
resource "alicloud_vpc" "myvpc" {
  vpc_name   = "demo-vpc"
  cidr_block = "172.16.0.0/12"
}

# 交换机
resource "alicloud_vswitch" "myvsw" {
  vpc_id     = alicloud_vpc.myvpc.id
  cidr_block = "172.16.0.0/24"
  zone_id    = var.zone_id
}

# 安全组
resource "alicloud_security_group" "web_sg" {
  name   = "web-sg"
  vpc_id = alicloud_vpc.myvpc.id
}

# 放行 SSH（生产建议限制来源 IP，不要对 0.0.0.0/0 全开）
resource "alicloud_security_group_rule" "allow_ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  port_range        = "22/22"
  security_group_id = alicloud_security_group.web_sg.id
  cidr_ip           = "0.0.0.0/0"
  policy            = "accept"
}

# ECS 实例
resource "alicloud_instance" "web" {
  image_id               = data.alicloud_images.ubuntu.images[0].id
  instance_type          = "ecs.e-c1m2.large"
  security_groups        = [alicloud_security_group.web_sg.id]
  vswitch_id             = alicloud_vswitch.myvsw.id
  instance_name          = "web-server-01"
  password               = var.instance_password
  internet_max_bandwidth_out = 5
  system_disk_category   = "cloud_essd_entry"
}
```

### 5.3 输出文件 outputs.tf

```hcl
output "instance_id" {
  value = alicloud_instance.web.id
}

output "public_ip" {
  value = alicloud_instance.web.public_ip
}
```

### 5.4 执行

```bash
terraform init
terraform plan -var="instance_password=你的强密码"
terraform apply -var="instance_password=你的强密码"
```

apply 成功后，输出里会给出实例公网 IP，即可 SSH 登录。日常建议把非敏感变量放进 `terraform.tfvars`，密码用环境变量 `TF_VAR_instance_password` 传入。

::: tip 规格与镜像随版本变化
实例规格（`instance_type`）、可用区、镜像命名会随阿里云更新而变化，若报错，先在控制台或文档确认当前可用的规格 ID 和可用区，再改代码。
:::

## 六、State 状态管理

### 6.1 state 的作用

state（默认 `terraform.tfstate`）记录 Terraform 管理的资源及其真实属性，是它判断"实际状态"和代码"期望状态"差异的依据。工作流中：`init` 建立 state 框架，`plan` 对比 state 与代码给出变更，`apply` 创建资源并把资源 ID、属性写入 state。

### 6.2 为什么要用远程后端

state 默认存在本地，团队协作时会有问题：多人各自保存、无法共享、可能同时 apply 造成冲突，且 state 里常含敏感信息。生产应配置**远程后端**：把 state 集中存储并**加锁**。

阿里云可用 OSS 存储 state、表格存储（Tablestore）做锁：

```hcl
terraform {
  backend "oss" {
    bucket              = "你的tfstate桶"
    prefix              = "demo/terraform.tfstate"
    region              = "cn-chengdu"
    tablestore_endpoint = "https://你的实例.cn-chengdu.ots.aliyuncs.com"
    tablestore_table    = "tf_lock"
  }
}
```

配置后执行 `terraform init`，按提示把本地 state 迁移到 OSS。之后一人 apply 时自动加锁，其他人需等待，避免并发冲突。AWS 对应 S3 + DynamoDB。

### 6.3 state 损坏与恢复

- 不要手工直接编辑 state；需要调整用 `terraform state` 子命令（如 `state rm`、`state mv`、`import`）；
- 远程 state 开启版本控制，误改后可回退到历史版本；
- state 文件损坏时，结合后端历史版本恢复，再用 `terraform plan` 核对与真实资源是否一致。

## 七、模块化

模块（Module）是把一组相关资源封装成可复用单元。比如把"VPC + 交换机"封装成网络模块，多个项目调用，避免重复编写。

```hcl
module "vpc" {
  source     = "./modules/network"   # 本地路径，也可用 Git/Registry
  vpc_name   = "demo-vpc"
  vpc_cidr   = "172.16.0.0/12"
}
```

模块设计原则：**单一职责**；通过输入变量接收差异、通过输出暴露结果；模块版本化管理，调用方锁定版本，避免模块变更影响已有环境。

## 八、团队协作规范

- state 放远程后端并加锁、开启版本控制；
- 基础设施代码走分支开发，提交前本地 `terraform plan`、`fmt`、`validate`；
- 变更通过 Merge Request 评审 plan 结果后再合并、再 apply；
- 生产 apply 由流水线或受控流程执行；回滚优先用代码版本回退 + apply，而非直接 destroy。

## 面试自测

1. 什么是基础设施即代码？相比手工在控制台操作有哪些优势？
2. Terraform 和 Ansible 的定位有什么区别？它们如何配合？
3. 说清 Terraform 的工作原理：HCL、state、CLI、Provider 如何协作。
4. 什么是 Provider？Terraform 怎么获取它？
5. Resource 的类型和名称如何唯一标识一个资源？
6. 什么是隐式依赖和显式依赖？Terraform 如何确定资源创建顺序？
7. HCL 中变量和输出分别解决什么问题？
8. 为什么敏感信息不能写进 .tf 文件并提交？应该怎么传？
9. 阿里云认证推荐用什么方式提供 AccessKey？对 RAM 子用户有什么要求？
10. 说清 init、plan、apply、destroy 各自的作用和执行时机。
11. plan 阶段会不会真正创建资源？
12. 用 Terraform 创建一台 ECS 需要哪些配套资源？
13. 如何避免硬编码镜像 ID？
14. state 文件的作用是什么？没有 state 会怎样？
15. 为什么团队协作要把 state 放到远程后端？
16. state 加锁解决什么问题？阿里云用什么产品实现存储和加锁？
17. 为什么不建议手工编辑 state？import 命令有什么用？
18. 什么是 Terraform 模块？模块设计应遵循哪些原则？
19. 团队里一次基础设施变更的标准流程是怎样的？
20. 如何回滚一次错误的基础设施变更？

## 相关速查

- 命令速查：[Linux 命令速查](/reference/linux-commands)
- 官方资源：
  - Terraform 官网：https://www.terraform.io/
  - Terraform CLI 文档：https://developer.hashicorp.com/terraform/docs
  - Terraform 下载：https://developer.hashicorp.com/terraform/install
  - 所有版本：https://releases.hashicorp.com/terraform/
  - HCL 语言：https://developer.hashicorp.com/terraform/language
  - 阿里云 Provider 文档：https://registry.terraform.io/providers/aliyun/alicloud/latest/docs
  - 阿里云 OSS Backend：https://developer.hashicorp.com/terraform/language/settings/backends/oss
  - 模块开发：https://developer.hashicorp.com/terraform/language/modules
  - Terraform Registry：https://registry.terraform.io/

