#!/bin/sh
# ==============================================================================
# 诈醒学集 — Nginx 启动入口
# Railway 会向容器注入 $PORT（动态端口）；本地 docker-compose 未设置时默认 80，
# 行为与原有配置保持一致。这里仅把 nginx 的 listen 端口替换为 $PORT，
# 其余 nginx 变量（$host / $uri / $proxy_add_x_forwarded_for 等）保持原样。
# ==============================================================================
set -e

PORT="${PORT:-80}"

# 将 `listen   80;` 改写为 `listen <PORT>;`（POSIX 正则，busybox sed 兼容）
sed -i "s/listen[[:space:]]*80;/listen ${PORT};/" /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
