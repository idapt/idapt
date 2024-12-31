#!/bin/sh
# Set the script to exit on error
set -e


# Create temporary directory for processing
mkdir -p /tmp/nginx-config

# Process nginx.conf with environment variables
envsubst '$HOST_DOMAIN' < /nginx-config-source/nginx.conf > /tmp/nginx-config/nginx.conf
cp /tmp/nginx-config/nginx.conf /etc/nginx/nginx.conf


# If there is user provided ssl certificates in the source folder, copy them to the intended location in the letsencrypt folder where nginx will look for them
# Note: there is a .gitinclude file in the certs folder so that the certs folder is created by git clone and does not throw an error during build, only do this option is there is actually .crt, .key or .pem files in the folder
if [ -n "$(find /nginx-certs-source -type f \( -name '*.crt' -o -name '*.key' -o -name '*.pem' \))" ]; then
    echo "User provided SSL certificates found."

    # If the certs are not already setup for this host_domain, generate them
    if [ ! -d /etc/letsencrypt/live/$HOST_DOMAIN ]; then
        
        echo "Copying user provided ssl certificates to the letsencrypt folder"
        # Create the letsencrypt folder if it doesn't exist
        mkdir -p /etc/letsencrypt/live/$HOST_DOMAIN
        
        # Convert certificates if they exist in .crt/.key format
        if [ -f /nginx-certs-source/*.crt ]; then
            echo "Converting .crt certificate to .pem format"
            openssl x509 -in /nginx-certs-source/*.crt -out /etc/letsencrypt/live/$HOST_DOMAIN/fullchain.pem
        fi
        if [ -f /nginx-certs-source/*.key ]; then
            echo "Converting .key certificate to .pem format"
            # Try to determine key type and handle accordingly
            if openssl rsa -in /nginx-certs-source/*.key -check -noout 2>/dev/null; then
                # It's an RSA key
                openssl rsa -in /nginx-certs-source/*.key -out /etc/letsencrypt/live/$HOST_DOMAIN/privkey.pem
            else
                # For other key types (EC, etc.), just copy directly
                cp /nginx-certs-source/*.key /etc/letsencrypt/live/$HOST_DOMAIN/privkey.pem
            fi
        fi
        
        # Or copy existing .pem files if they exist
        if [ -f /nginx-certs-source/fullchain.pem ]; then
            echo "Copying fullchain.pem to the letsencrypt folder"
            cp /nginx-certs-source/fullchain.pem /etc/letsencrypt/live/$HOST_DOMAIN/
        fi
        if [ -f /nginx-certs-source/privkey.pem ]; then
            echo "Copying privkey.pem to the letsencrypt folder"
            cp /nginx-certs-source/privkey.pem /etc/letsencrypt/live/$HOST_DOMAIN/
        fi
    fi

    # Process normal server.conf with environment variables
    envsubst '$HOST_DOMAIN' < /nginx-config-source/server.conf > /tmp/nginx-config/server.conf
    cp /tmp/nginx-config/server.conf /etc/nginx/conf.d/server.conf

    # Just start nginx now that the custom certificates are in place and dont use certbot
    echo "Starting nginx without certbot support"
    nginx -g 'daemon off;'

# Else if the app is running in local mode
elif [ "$HOST_DOMAIN" = "localhost" ]; then

    # Copy the server-local.conf to the nginx conf.d folder
    cp /nginx-config-source/server-local.conf /etc/nginx/conf.d/server-local.conf

    # Use the original entrypoint script of the image nginx-certbot that will use Local CA and manage renewals as USE_LOCAL_CA=1
    echo "Starting nginx with local cert"
    exec /scripts/start_nginx_certbot.sh

# Else the app is remote and have no provided ssl certificates
else

    # Process normal server.conf with environment variables
    envsubst '$HOST_DOMAIN' < /nginx-config-source/server.conf > /tmp/nginx-config/server.conf
    cp /tmp/nginx-config/server.conf /etc/nginx/conf.d/server.conf


    # Use the original entrypoint script of the image nginx-certbot
    echo "Starting nginx with certbot support that will generate the certificates for domain $HOST_DOMAIN"
    exec /scripts/start_nginx_certbot.sh
fi