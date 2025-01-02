FROM jonasal/nginx-certbot:5.4.0-alpine

# Install required packages for envsubst and proper SSL handling
RUN apk add --no-cache gettext

# Copy nginx config
RUN mkdir -p /nginx-config-source
# Copy all of the nginx config from the host build directory
COPY ./config/ /nginx-config-source/
RUN chmod 775 /nginx-config-source/*

# The user provided ssl certificates for dev only
# Copy user provided nginx ssl certificates
RUN mkdir -p /nginx-certs-source
# Copy all of the certs folder from the host
COPY ./certs/ /nginx-certs-source/
# Only chmod files if they exist
RUN find /nginx-certs-source -type f -exec chmod 775 {} + || true

# Copy the dev entrypoint script and make it executable
COPY dev.entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the custom entrypoint script of the image
ENTRYPOINT ["/entrypoint.sh"]