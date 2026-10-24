# Production-ready, lightweight Dockerfile
FROM nginx:alpine

# Metadata
LABEL maintainer="TONN Sievphor <tonnsievphor@gmail.com>"
LABEL project="USEA Advanced Cloud Technology - Homework 3"

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy application static files
COPY index.html .

# Expose standard HTTP port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
