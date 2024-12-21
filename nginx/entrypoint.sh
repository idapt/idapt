#!/bin/sh
set -e

# Create required directories
mkdir -p /config/nginx/certs
mkdir -p /var/www/certbot
mkdir -p /var/log
mkdir -p /root/.cache # Cron directory

# Copy configuration files from source to not override them
cp -r /nginx-config-source/* /config/nginx/

# Replace environment variables in all of the configuration files
envsubst '$HOST_DOMAIN' < /nginx-config-source/nginx.conf > /etc/nginx/nginx.conf
envsubst '$HOST_DOMAIN' < /nginx-config-source/kc-proxy-set-headers.conf > /etc/nginx/kc-proxy-set-headers.conf


# Function to check if domain is local
is_local_domain() {
    domain=$1
    case $domain in
        localhost|0.0.0.0|127.0.0.1) return 0 ;;
        192.168.*.*) return 0 ;;
        *) return 1 ;;
    esac
}

# Certificate setup - only if not already done
if [ -f "/etc/letsencrypt/live/${HOST_DOMAIN}/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/${HOST_DOMAIN}/privkey.pem" ]; then
    echo "Using existing certificates..."
else
    # If there are certificates in the source directory, use them.
    if [ -f "/nginx-certs-source/${HOST_DOMAIN}.crt" ] && [ -f "/nginx-certs-source/${HOST_DOMAIN}.key" ]; then
        echo "Using existing certificates from source..."
        mkdir -p /etc/letsencrypt/live/${HOST_DOMAIN}
        
        cp "/nginx-certs-source/${HOST_DOMAIN}.crt" "/etc/letsencrypt/live/${HOST_DOMAIN}/fullchain.pem"
        cp "/nginx-certs-source/${HOST_DOMAIN}.key" "/etc/letsencrypt/live/${HOST_DOMAIN}/privkey.pem"
        cp "/nginx-certs-source/${HOST_DOMAIN}.crt" "/etc/letsencrypt/live/${HOST_DOMAIN}/chain.pem"
    
    # If the domain is local, generate a self-signed certificate using openssl.
    elif is_local_domain "${HOST_DOMAIN}"; then
        echo "Generating self-signed certificate for local domain..."
        mkdir -p /etc/letsencrypt/live/${HOST_DOMAIN}
        
        # Generate self-signed certificate for local domain
        openssl req -x509 \
            -out "/etc/letsencrypt/live/${HOST_DOMAIN}/fullchain.pem" \
            -keyout "/etc/letsencrypt/live/${HOST_DOMAIN}/privkey.pem" \
            -newkey rsa:2048 -nodes -sha256 \
            -subj "/CN=${HOST_DOMAIN}" -extensions EXT -config <( \
            printf "[dn]\nCN=${HOST_DOMAIN}\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:${HOST_DOMAIN}\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")
        
        # Copy the certificate to chain.pem as well
        cp "/etc/letsencrypt/live/${HOST_DOMAIN}/fullchain.pem" "/etc/letsencrypt/live/${HOST_DOMAIN}/chain.pem"
        
        echo "Self-signed certificates generated successfully"

    # If the domain is not local, request a certificate from Let's Encrypt.
    else
        echo "Requesting certificate from Let's Encrypt..."
        
        if [ -z "${CERTBOT_EMAIL}" ]; then
            echo "Error: CERTBOT_EMAIL environment variable is required for initial certificate request"
            exit 1
        fi

        # Request initial certificate
        certbot certonly --webroot \
            --webroot-path=/var/www/certbot \
            --email ${CERTBOT_EMAIL} \
            --agree-tos \
            --no-eff-email \
            -d ${HOST_DOMAIN}
            
        if [ $? -ne 0 ]; then
            echo "Failed to obtain initial certificate"
            exit 1
        fi
    fi
    
    echo "Certificate initialization completed"
fi

# Only set up cron for non-local domains if not already setup
if ! is_local_domain "${HOST_DOMAIN}"; then
    if ! crontab -l | grep -q "/renew-cert.sh"; then
        crond
        
        # Generate random hour (0-23) and minute (0-59)
        RANDOM_HOUR=$(( RANDOM % 24 ))
        RANDOM_MINUTE=$(( RANDOM % 60 ))
        
        # Setup renewal cron job
        echo "${RANDOM_MINUTE} ${RANDOM_HOUR} */30 * * /renew-cert.sh >> /var/log/cert-renewal.log 2>&1" | crontab -
        
        echo "Cron setup completed"
    else
        echo "Cron job already set up, skipping"
    fi
fi

# Start nginx in foreground
exec nginx -g 'daemon off;'