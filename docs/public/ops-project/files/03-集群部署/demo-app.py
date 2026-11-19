#!/usr/bin/env python3
# ============================================================
# P1 占位应用：验证 "VIP → Nginx → App → MySQL / Redis" 全链路
# 部署路径：/opt/edu-app/app.py
# P3 阶段会被真正的 SpringCloud 微服务 + Harbor 镜像替换
# ============================================================
import os
import socket

import pymysql
import redis
from flask import Flask, Response

APP_VERSION = os.getenv("APP_VERSION", "v1")

DB = dict(
    host=os.getenv("DB_HOST", "10.0.0.150"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "edu"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "edu"),
    charset="utf8mb4",
    connect_timeout=2,
)

def make_redis():
    """优先走哨兵；没配哨兵就直接连单机（P1 的用法）。"""
    sentinels = os.getenv("REDIS_SENTINELS", "").strip()
    if sentinels:
        from redis.sentinel import Sentinel

        nodes = []
        for item in sentinels.split(","):
            host, _, port = item.partition(":")
            nodes.append((host, int(port or 26379)))
        sentinel = Sentinel(nodes, socket_timeout=2)
        return sentinel.master_for(
            os.getenv("REDIS_MASTER_NAME", "mymaster"),
            decode_responses=True,
            socket_timeout=2,
        )
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "10.0.0.160"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        socket_timeout=2,
        decode_responses=True,
    )


RC = make_redis()

app = Flask(__name__)


@app.get("/")
def index():
    db_ok = False
    try:
        with pymysql.connect(**DB) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM course")
                courses = cur.fetchone()[0]
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        courses = f"error: {exc}"

    try:
        visits = RC.incr("edu:visits")
    except Exception as exc:  # noqa: BLE001
        visits = f"error: {exc}"

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Edu Platform</title></head>
<body style="font-family:system-ui;max-width:680px;margin:60px auto;line-height:1.8">
<h1>在线教育平台 · 实验环境</h1>
<table cellpadding="6">
  <tr><td>版本</td><td><b>{APP_VERSION}</b></td></tr>
  <tr><td>应用节点</td><td>{socket.gethostname()}</td></tr>
  <tr><td>MySQL 课程数</td><td>{courses}</td></tr>
  <tr><td>Redis 访问计数</td><td>{visits}</td></tr>
  <tr><td>数据库连通</td><td>{'YES' if db_ok else 'NO'}</td></tr>
</table>
<p style="color:#888">P1 占位应用，P3 将替换为 SpringCloud 微服务</p>
</body></html>"""
    return Response(html, mimetype="text/html")


@app.get("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
