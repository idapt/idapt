FROM nginx:alpine

# Install required packages
RUN apk add --no-cache gettext certbot certbot-nginx cronie openssl

# Create required directories
RUN mkdir -p /var/www/certbot

COPY entrypoint.sh /entrypoint.sh
COPY renew-cert.sh /renew-cert.sh
RUN chmod +x /entrypoint.sh /renew-cert.sh

ENTRYPOINT ["/entrypoint.sh"]