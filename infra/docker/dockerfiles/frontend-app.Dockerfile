# syntax=docker/dockerfile:1.7

FROM node:22-alpine AS build
WORKDIR /workspace

COPY apps/web/frontend-app/package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY apps/web/frontend-app/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY infra/nginx/frontend-app.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
