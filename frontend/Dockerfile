# Stage 1 — build the static React bundle
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests first so Docker can cache the install layer.
COPY package.json package-lock.json* ./
RUN npm install

# Copy source and build.
COPY . .
RUN npm run build

# Stage 2 — serve the bundle with nginx
FROM nginx:1.27-alpine

# Replace the default nginx config so:
#   /         -> serve the React SPA (with HTML5 history fallback)
#   /ask      -> proxy to the backend FastAPI service
#   /priority -> proxy to the backend
#   /store    -> proxy to the backend
#   /search   -> proxy to the backend
#   /ingest   -> proxy to the backend
#   /health   -> proxy to the backend
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
