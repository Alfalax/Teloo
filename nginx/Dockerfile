FROM nginx:alpine

# Remove default configuration
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Health check - only checks nginx itself, not backend services
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=30s \
  CMD wget --quiet --tries=1 --spider http://localhost:80/health || exit 1
