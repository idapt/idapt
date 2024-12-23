#!/bin/bash

# Create secrets directory if it doesn't exist
mkdir -p /postgres_admin_secrets
mkdir -p /postgres_backend_secrets
mkdir -p /postgres_keycloak_secrets

# Function to generate a random password if it doesn't exist
generate_password() {
    local file=$1
    
    if [ ! -f "$file" ]; then
        (tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32) > "$file"
        echo "Generated new password in $file"
    else
        echo "Password already exists in $file"
    fi
}

# Set or generate admin password based on DEV_DB_PASSWORD
if [ -n "$DEV_DB_PASSWORD" ]; then
    echo "$DEV_DB_PASSWORD" > "/postgres_admin_secrets/POSTGRES_PASSWORD"
    echo "Using DEV_DB_PASSWORD for admin password"
else
    generate_password "/postgres_admin_secrets/POSTGRES_PASSWORD"
fi

# Generate passwords for other users
generate_password "/postgres_backend_secrets/IDAPT_BACKEND_PASSWORD"
generate_password "/postgres_keycloak_secrets/IDAPT_KEYCLOAK_PASSWORD"

# Set environment variables for postgres password
export POSTGRES_PASSWORD=$(cat /postgres_admin_secrets/POSTGRES_PASSWORD)
export IDAPT_BACKEND_PASSWORD=$(cat /postgres_backend_secrets/IDAPT_BACKEND_PASSWORD)
export IDAPT_KEYCLOAK_PASSWORD=$(cat /postgres_keycloak_secrets/IDAPT_KEYCLOAK_PASSWORD)

# If the init-users-db.sql file doesn't exist, process the template and create it
if [ ! -f "/docker-entrypoint-initdb.d/init-users-db.sql" ]; then
    envsubst < /docker-entrypoint-initdb.d/init-users-db.sql.template > /docker-entrypoint-initdb.d/init-users-db.sql
fi

# Start postgres with the original entrypoint
exec docker-entrypoint.sh postgres