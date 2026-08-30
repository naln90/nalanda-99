# ==============================================================================
# 防诈智研 — 前端 Dockerfile (多阶段构建: Node 构建 + Nginx 部署)
# ==============================================================================

# ---------- Stage 1: 构建前端 ----------
FROM node:22-alpine AS builder

WORKDIR /app

# 利用 Docker 缓存：先拷依赖文件
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

# 拷源码并构建
COPY . .

# 注入前端 API 基地址：容器内走 nginx 反代 /api 到后端；
# 如需独立域名部署，构建时覆盖：docker compose build --build-arg VITE_API_BASE_URL=https://your-domain.com/api
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ---------- Stage 2: Nginx 部署 ----------
FROM nginx:alpine

# 拷贝自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 拷贝构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
