# Advisor Frontend Dockerfile - Production-ready multi-stage build

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

# Build the application for production
RUN npm run build

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
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3001 || exit 1

# Development command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"]

# Stage 4: Production (for future use)
FROM node:18-slim AS production
WORKDIR /app

ENV NODE_ENV=production

# Install only curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy built assets from builder
COPY --from=builder /app/dist ./dist
COPY --from=deps /app/node_modules ./node_modules
COPY package.json ./

# Create non-root user
RUN groupadd -g 1001 nodejs && \
    useradd -r -u 1001 -g nodejs nextjs && \
    chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001 || exit 1

# Production command (serve built files)
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3001"]
