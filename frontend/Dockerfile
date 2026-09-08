# ==========================================
# 阶段 1: 静态编译构建环境
# ==========================================
FROM node:22-alpine AS builder

WORKDIR /app

# 利用 Docker 层缓存加速依赖安装
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码并编译生产包
COPY . .
RUN npm run build

# ==========================================
# 阶段 2: 极小化 Nginx 生产运行环境
# ==========================================
FROM nginx:1.27-alpine AS runner

# 移除默认配置并挂载自定义 SPA 配置文件
RUN rm -rf /etc/nginx/conf.d/default.conf /usr/share/nginx/html/*
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
