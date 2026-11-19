# -*- coding: utf-8 -*-
import re
from pathlib import Path

DOCS = Path(r"D:\Develop\static-blog\docs")
KEEP = [
    "t-nginx-502", "t-nginx-504-timeout", "t-mysql-replica-lag", "t-mysql-deadlock", "t-mysql-slow-query",
    "t-redis-sentinel-failover", "t-redis-memory-oom", "t-docker-daemon-fail", "t-docker-network-bridge",
    "t-docker-storage-driver", "t-k8s-pod-pending", "t-k8s-crashloopbackoff", "t-k8s-node-notready",
    "t-k8s-etcd-failure", "t-k8s-imagepullbackoff", "t-dns-resolution-fail", "t-tcp-retransmission",
    "t-disk-space-full", "t-process-d-state-hang", "t-mining-trojan",
]
for stem in KEEP:
    p = DOCS / "cases" / (stem + ".md")
    text = p.read_text(encoding="utf-8")
    mt = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
    md = re.search(r"^description:\s*[\"']?(.+?)[\"']?\s*$", text, re.M)
    print(stem, "|", mt.group(1).strip() if mt else "", "|", md.group(1).strip() if md else "")
