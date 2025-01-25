#!/bin/sh
# Set the script to exit on error
set -e

# Process nginx.conf with environment variables
envsubst '$HOST_DOMAIN $FRONTEND_PORT $API_PORT' < /nginx-config-source/nginx.conf > /etc/nginx/nginx.conf

# If environment is dev, process dev-server.conf with environment variables
if [ "$ENVIRONMENT" = "dev" ]; then
    envsubst '$HOST_DOMAIN $FRONTEND_PORT $API_PORT' < /nginx-config-source/dev-server.conf > /etc/nginx/conf.d/dev-server.conf
# If deployment type is hosted, process local-frontend-server.conf with environment variables
elif [ "$DEPLOYMENT_TYPE" = "hosted" ]; then
    envsubst '$HOST_DOMAIN $FRONTEND_PORT $API_PORT' < /nginx-config-source/local-frontend-server.conf > /etc/nginx/conf.d/local-frontend-server.conf
else
    # Else process server.conf with environment variables
    envsubst '$HOST_DOMAIN $FRONTEND_PORT $API_PORT' < /nginx-config-source/server.conf > /etc/nginx/conf.d/server.conf
fi


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
# Else if there is no user provided ssl certificates, create a self signed certificate with infinite validity using openssl
else
    echo "No user provided ssl certificates found"
    # If there is existing self signed certificate at the intended location, don't generate new ones, it will make it so that we dont need to accept the warning in the browser each time we update the container
    if [ ! -f /etc/letsencrypt/live/$HOST_DOMAIN/fullchain.pem ]; then
        echo "Creating self signed ssl certificate with infinite validity using openssl"
        # Create the letsencrypt folder if it doesn't exist
        mkdir -p /etc/letsencrypt/live/$HOST_DOMAIN
        openssl req -x509 -newkey rsa:4096 -keyout /etc/letsencrypt/live/$HOST_DOMAIN/privkey.pem -out /etc/letsencrypt/live/$HOST_DOMAIN/fullchain.pem -days 365000 -nodes -subj "/CN=$HOST_DOMAIN"
    else
        echo "Self signed ssl certificate already exists at the intended location"
    fi
fi


# Start nginx
echo "Starting nginx"
nginx -g 'daemon off;'