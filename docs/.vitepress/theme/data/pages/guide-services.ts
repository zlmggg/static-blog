import type { Article } from '../types'

const articles: Article[] = [
  {
    group: 'Web 服务',
    title: 'Nginx 实战',
    link: '/guide/services-web-nginx',
    sub: '安装、虚拟主机、反向代理、负载均衡、SSL/HTTP2、调优'
  },
  {
    group: 'Web 服务',
    title: 'Apache 与 Tomcat',
    link: '/guide/services-web-apache-tomcat',
    sub: 'HTTP 协议、Apache 虚拟主机/认证、Tomcat、JVM/GC'
  },
  {
    group: 'DNS 域名服务',
    title: 'DNS 域名解析',
    link: '/guide/services-dns',
    sub: 'DNS 原理/记录、BIND 部署、正反解析、主从、分离解析'
  },
  {
    group: '文件共享',
    title: '文件共享服务',
    link: '/guide/services-file-sharing',
    sub: 'NFS、Samba、vsftpd 部署与权限'
  },
  {
    group: '负载均衡与高可用',
    title: 'LVS 与 Keepalived',
    link: '/guide/services-lvs-keepalived',
    sub: 'LVS DR/NAT 模式、ipvsadm、Keepalived VIP 四层负载高可用'
  }
]

export default articles
