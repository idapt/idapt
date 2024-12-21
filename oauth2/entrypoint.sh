#!/bin/bash

# Generate cookie secret if it doesn't exist
if [ ! -f "/oauth2_cookie_secret/OAUTH2_PROXY_COOKIE_SECRET" ]; then
    echo "Generating new OAuth2 proxy cookie secret..."
    dd if=/dev/urandom bs=32 count=1 2>/dev/null | base64 | tr -d -- '\n' | tr -- '+/' '-_' > /oauth2_cookie_secret/OAUTH2_PROXY_COOKIE_SECRET
    echo "Cookie secret generated successfully"
else
    echo "Cookie secret already exists"
fi

# Function to wait for client secret file
wait_for_client_secret() {
    local secret_file="/keycloak_oauth2_client_secret/OAUTH2_PROXY_CLIENT_SECRET"
    until [ -f "$secret_file" ] && [ -r "$secret_file" ] && [ -s "$secret_file" ]; do
        echo "Waiting for Keycloak client secret..."
        sleep 5
    done
    echo "Client secret is available"
}

# Wait for client secret to be available
wait_for_client_secret

# Export the cookie secret as file path is not supported
export OAUTH2_PROXY_COOKIE_SECRET=$(cat /oauth2_cookie_secret/OAUTH2_PROXY_COOKIE_SECRET)

# Replace environment variables in the config file
envsubst < /oauth2-proxy.cfg > /etc/oauth2-proxy/oauth2-proxy.cfg

# Start oauth2-proxy with the config file
exec /bin/oauth2-proxy --config=/etc/oauth2-proxy/oauth2-proxy.cfg