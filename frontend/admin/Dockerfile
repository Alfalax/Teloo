# Admin Frontend Dockerfile - Production-ready multi-stage build

# Stage 1: Dependencies
FROM node:18-slim AS deps
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Stage 2: Builder (for production builds)
FROM node:18-slim AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application for production (skip TypeScript check for faster builds)
# Set NODE_OPTIONS to limit memory usage in constrained environments
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm run build:prod

# Stage 3: Development
FROM node:18-slim AS development
WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev dependencies for Vite)
RUN npm ci

# Manually install the correct Rollup binary for Linux x64 GNU
RUN npm install --no-save @rollup/rollup-linux-x64-gnu

# Copy source code
COPY . .

# Create non-root user
RUN groupadd -g 1001 nodejs && \
    useradd -r -u 1001 -g nodejs nextjs && \
    chown -R nextjs:nodejs /app

USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Development command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Stage 4: Production (Serve with Nginx + API Proxy)
FROM nginx:alpine AS production

# Copy built assets from builder
COPY --from=builder /app/dist /app/dist

# Copy custom nginx configuration template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy custom entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN apk add --no-cache dos2unix && dos2unix /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Expose port 80 (Standard web port)
EXPOSE 80

# Healthcheck for Nginx
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]



