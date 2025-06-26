# 构建阶段
FROM hub.kingschats.com/node:18-alpine AS build-stage

WORKDIR /app

# 配置npm阿里云镜像源
RUN npm config set registry https://registry.npmmirror.com/

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM hub.kingschats.com/nginx:alpine AS production-stage

# 复制构建产物到nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"] 