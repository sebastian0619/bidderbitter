#!/bin/sh
set -e

# 默认值
: "${MAX_UPLOAD_SIZE_MB:=50}"

# 渲染nginx.conf
envsubst '$MAX_UPLOAD_SIZE_MB' < /etc/nginx/conf.d/default.conf > /etc/nginx/conf.d/default.conf.tmp
mv /etc/nginx/conf.d/default.conf.tmp /etc/nginx/conf.d/default.conf

echo "========= 渲染后的nginx.conf ========="
cat /etc/nginx/conf.d/default.conf

echo "========= 检查nginx配置语法 ========="
if ! nginx -t; then
  echo "nginx配置有误，容器退出"
  exit 1
fi

echo "========= 启动nginx ========="
exec nginx -g 'daemon off;' 