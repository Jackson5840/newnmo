# ---- Build stage ----
FROM node:16-bullseye AS build

WORKDIR /app

# Install deps first (better layer caching)
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# Copy source and build
COPY scripts ./scripts
COPY src ./src

# Override the hard-coded API base URL with the value provided at build time.
# Defaults to "/api" so the frontend works behind the nginx reverse proxy.
ARG API_BASE_URL=/api
RUN sed -i "s|^const apiurlbase = .*|const apiurlbase = '${API_BASE_URL}';|" src/js/base.js

RUN npm run build


# ---- Runtime stage ----
FROM nginx:1.25-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
