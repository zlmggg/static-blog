import type { Article } from '../types'

const articles: Article[] = [
  {
    group: '入门与基础',
    title: '安装与初始环境',
    link: '/guide/linux-install',
    sub: '装系统、虚拟机、配 IP/SSH/软件源、发行版差异'
  },
  {
    group: '入门与基础',
    title: '文件系统',
    link: '/guide/linux-filesystem',
    sub: 'FHS 目录、文件类型、inode、软硬链接、挂载'
  },
  {
    group: '入门与基础',
    title: '磁盘存储',
    link: '/guide/linux-storage',
    sub: '分区、格式化、LVM、RAID、磁盘配额'
  },
  {
    group: '用户与权限',
    title: '用户与权限',
    link: '/guide/linux-users',
    sub: '用户组管理、rwx、特殊权限、ACL、sudo、LDAP'
  },
  {
    group: '进程与任务',
    title: '进程与服务',
    link: '/guide/linux-process',
    sub: 'systemd 服务管理、进程查看/控制、前后台、优先级'
  },
  {
    group: '进程与任务',
    title: '定时任务',
    link: '/guide/linux-cron',
    sub: 'crontab、at、systemd timer'
  },
  {
    group: '进程与任务',
    title: '性能排查',
    link: '/guide/linux-performance',
    sub: 'top/ps/vmstat/iostat/pidstat、USE 方法、CPU/内存/IO/网络四类瓶颈实战'
  },
  {
    group: '内核与日志',
    title: '内核调优',
    link: '/guide/linux-kernel',
    sub: 'sysctl 参数、内核模块、ulimit 资源限制'
  },
  {
    group: '内核与日志',
    title: '日志管理',
    link: '/guide/linux-log',
    sub: '日志分类、journalctl、rsyslog、logrotate、dmesg'
  },
  {
    group: '编程与安全',
    title: 'Shell 脚本编程',
    link: '/guide/linux-shell',
    sub: '语法、条件、循环、函数、数组、调试、生产脚本'
  },
  {
    group: '编程与安全',
    title: '安全加固',
    link: '/guide/linux-security',
    sub: '防火墙、SELinux、SSH 加固、SSL、VPN、NTP'
  },
  {
    group: '编程与安全',
    title: 'iptables 防火墙',
    link: '/guide/linux-security-iptables',
    sub: 'iptables 四表五链、规则编写实战'
  },
  {
    group: 'eBPF 与内核前沿',
    title: 'eBPF 原理与应用',
    link: '/guide/linux-ebpf',
    sub: 'eBPF 验证器/Maps、bcc/bpftrace、Cilium 数据面、可观测与安全'
  },
  {
    group: '网络基础',
    title: '网络基础',
    link: '/guide/linux-network',
    sub: 'OSI/TCP-IP 分层、IP 地址与子网划分、TCP/UDP、以太网 MAC、Linux 网卡配置、bond 高可用'
  }
]

export default articles
