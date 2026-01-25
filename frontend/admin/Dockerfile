# Admin Frontend Dockerfile - Simple and working
FROM node:18-slim

# Cache buster
ARG CACHE_BUST=2026-01-24-v3

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build:prod

# Install serve and curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* && npm install -g serve

# Expose port
EXPOSE 9008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9008 || exit 1

# Start
CMD ["serve", "-s", "dist", "-l", "9008"]
