#!/bin/sh

# Function to check if domain is local
is_local_domain() {
    domain=$1
    case $domain in
        localhost|0.0.0.0|127.0.0.1) return 0 ;;
        192.168.*.*) return 0 ;;
        *) return 1 ;;
    esac
}

# Function to attempt certificate renewal
renew_certificate() {
    # Skip renewal for local domains
    if is_local_domain "${HOST_DOMAIN}"; then
        echo "Skipping certificate renewal for local domain"
        return 0
    fi

    while true; do
        echo "Attempting certificate renewal..."
        
        certbot renew --webroot \
            --webroot-path=/var/www/certbot \
            --deploy-hook "nginx -s reload" \
            --quiet

        if [ $? -eq 0 ]; then
            echo "Certificate renewal successful."
            break
        else
            echo "Certificate renewal failed. Retrying in 6 hours..."
            sleep 21600  # Sleep for 6 hours (6 * 60 * 60 seconds)
        fi
    done
}

# Call the renewal function
renew_certificate