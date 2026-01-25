# Admin Frontend Dockerfile - Simple and working
FROM node:18-slim

# Cache buster
ARG CACHE_BUST=2026-01-24-v1

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Install serve
RUN npm install -g serve

# Expose port
EXPOSE 9008

# Start
CMD ["serve", "-s", "dist", "-l", "9008"]
