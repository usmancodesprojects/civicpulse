FROM node:22.13.1-alpine3.21 AS builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY tsconfig*.json vite.config.ts vitest.config.ts eslint.config.js index.html ./
COPY src ./src
RUN npm run build

FROM nginx:1.31.6-alpine3.24 AS runtime
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /build/dist /usr/share/nginx/html
RUN chown -R 101:101 /usr/share/nginx/html
USER 101:101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
CMD ["nginx", "-g", "daemon off;"]

