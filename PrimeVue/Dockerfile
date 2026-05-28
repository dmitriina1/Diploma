# Multi-stage build для production
FROM node:18-alpine AS builder

WORKDIR /app

ARG VITE_ADMIN_ANALYTICS_URL="http://localhost:3035"
ENV VITE_ADMIN_ANALYTICS_URL=$VITE_ADMIN_ANALYTICS_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage - nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
