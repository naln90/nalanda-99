# ==============================================================================
# 诈醒学集 — 仓库根 Dockerfile（供 Railway / Railpack 从仓库根构建使用）
# ------------------------------------------------------------------------------
# 真实源码在 01_source_main_demo/fraud-pet-demo 子目录。Railpack 默认扫描仓库根，
# 因此在根目录放一个 Dockerfile，把该子目录作为构建上下文来构建前端并交付。
# 若不希望用根 Dockerfile，也可在 Railway 服务设置里把 Root Directory 指向
# 01_source_main_demo/fraud-pet-demo（那样会改用子目录里的 Dockerfile）。
# ==============================================================================

# ---------- Stage 1: 构建前端 ----------
FROM node:22-alpine AS builder

WORKDIR /app

# 利用 Docker 缓存：先拷依赖文件
COPY 01_source_main_demo/fraud-pet-demo/package.json 01_source_main_demo/fraud-pet-demo/package-lock.json* ./
RUN npm ci --no-audit --no-fund

# 拷源码并构建
COPY 01_source_main_demo/fraud-pet-demo/ ./

# 注入前端 API 基地址：容器内走 nginx 反代 /api 到后端；
# 如需独立域名部署，构建时覆盖：docker build --build-arg VITE_API_BASE_URL=https://your-domain.com/api
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ---------- Stage 2: Nginx 部署 ----------
FROM nginx:alpine

# 拷贝自定义 Nginx 配置与启动入口（入口会把监听端口改为 Railway 注入的 $PORT）
COPY 01_source_main_demo/fraud-pet-demo/nginx.conf /etc/nginx/conf.d/default.conf
# Railway 单容器没有 `backend` 服务，nginx 启动时解析该主机名会失败。
# 改为指向本机 127.0.0.1，保证 nginx 能正常启动；运行时 /api/ 会 502（预期，无后端）。
RUN sed -i 's|proxy_pass http://backend:8000/api/;|proxy_pass http://127.0.0.1:8000/api/;|' /etc/nginx/conf.d/default.conf
COPY 01_source_main_demo/fraud-pet-demo/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 拷贝构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
