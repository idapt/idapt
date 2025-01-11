# Build frontend
FROM node:23-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.* ./
RUN npm install
COPY frontend/ .
RUN npm run build




FROM nginx:1.27.3-alpine

# Install required packages for envsubst and proper SSL handling
RUN apk add --no-cache gettext openssl

# Copy nginx config
RUN mkdir -p /nginx-config-source
# Copy all of the nginx config from the host build directory
COPY nginx/config/ /nginx-config-source/
RUN chmod 775 /nginx-config-source/*

# Copy user provided nginx ssl certificates
RUN mkdir -p /nginx-certs-source
# Copy all of the certs folder from the host
COPY nginx/certs/ /nginx-certs-source/
# Only chmod files if they exist
RUN find /nginx-certs-source -type f -exec chmod 775 {} + || true

# Copy frontend static files
COPY --from=frontend-build /frontend/out /usr/share/nginx/html

# Copy entrypoint script and make it executable
COPY nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the custom entrypoint script of the image
ENTRYPOINT ["/entrypoint.sh"]