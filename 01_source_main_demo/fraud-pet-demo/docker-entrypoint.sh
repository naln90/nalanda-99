#!/bin/sh
# ==============================================================================
# 诈醒学集 — Nginx 启动入口
# Railway 会向容器注入 $PORT（动态端口）；本地 docker-compose 未设置时默认 80。
# 使用 envsubst 将 nginx.conf 中的 ${PORT} 替换为实际端口，避免 sed 正则失效。
# ==============================================================================
set -e

PORT="${PORT:-80}"
export PORT

# 用 envsubst 替换 ${PORT}，生成最终 nginx 配置
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf > /etc/nginx/conf.d/default.conf.tmp
mv /etc/nginx/conf.d/default.conf.tmp /etc/nginx/conf.d/default.conf

# 校验配置语法（若失败直接退出，便于日志排查）
nginx -t

exec nginx -g 'daemon off;'
