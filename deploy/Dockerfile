# ---- 构建阶段：安装依赖并编译 VitePress ----
FROM node:20-alpine AS builder
WORKDIR /app

# 先复制依赖清单，充分利用 Docker 层缓存
COPY package.json package-lock.json ./
# 构建需要 devDependencies（vitepress / mermaid / markdown-it-container），不能加 --omit=dev
RUN npm ci

# 复制站点内容并构建（产物在 docs/.vitepress/dist）
COPY docs ./docs
RUN npm run build

# ---- 运行阶段：Nginx 托管纯静态产物 ----
FROM nginx:alpine

# 静态站点 Nginx 配置（gzip / 缓存 / 路由回退）
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段拷贝静态产物
COPY --from=builder /app/docs/.vitepress/dist /usr/share/nginx/html

EXPOSE 80

# 存活探针：每 30s 探测 /health，连续失败会触发编排器（docker/compose）重启
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
