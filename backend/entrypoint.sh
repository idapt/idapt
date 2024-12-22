#!/bin/bash

# Function to wait for client secret file
wait_for_client_secret() {
    local secret_file="/keycloak_backend_client_secret/BACKEND_CLIENT_SECRET"
    until [ -f "$secret_file" ] && [ -r "$secret_file" ] && [ -s "$secret_file" ]; do
        echo "Waiting for Keycloak client secret..."
        sleep 1
    done
    echo "Client secret is available"
}

# Wait for client secret to be available
wait_for_client_secret

# Start the backend application
exec "$@"