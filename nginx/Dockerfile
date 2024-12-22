FROM nginx:alpine

# Install required packages
RUN apk add --no-cache gettext certbot certbot-nginx cronie openssl

# Create required directories
RUN mkdir -p /var/www/certbot

# Copy nginx config
RUN mkdir -p /nginx-config-source
# Copy all of the nginx config from the host
COPY ./config/ /nginx-config-source/
RUN chmod 775 /nginx-config-source/*

# Copy nginx ssl certificates
RUN mkdir -p /nginx-certs-source
# Copy all of the certs folder from the host
COPY ./certs/ /nginx-certs-source/
RUN chmod 775 /nginx-certs-source/*

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
COPY renew-cert.sh /renew-cert.sh
RUN chmod +x /entrypoint.sh /renew-cert.sh

ENTRYPOINT ["/entrypoint.sh"]