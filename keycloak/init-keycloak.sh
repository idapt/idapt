#!/bin/bash

# Get the admin password from the entrypoint script first argument
KEYCLOAK_TEMP_ADMIN_PASSWORD=$1
echo "Keycloak temp admin password: $KEYCLOAK_TEMP_ADMIN_PASSWORD"

# Get the user email from the entrypoint script second argument
KEYCLOAK_USER_EMAIL=$2
echo "Keycloak user email: $KEYCLOAK_USER_EMAIL"

# Get the dev mode settings
DEV_SET_INITIAL_KEYCLOAK_ADMIN_PASSWORD=$3
echo "Dev set initial keycloak admin password: $DEV_SET_INITIAL_KEYCLOAK_ADMIN_PASSWORD"
DEV_INITIAL_KEYCLOAK_ADMIN_PASSWORD=$4
echo "Dev initial keycloak admin password: $DEV_INITIAL_KEYCLOAK_ADMIN_PASSWORD"

# Function to wait for Keycloak to be ready
wait_for_keycloak() {
    until exec 3<>/dev/tcp/127.0.0.1/9000 && \
          echo -e "GET /auth/health/ready HTTP/1.1\r\nhost: localhost\r\nConnection: close\r\n\r\n" >&3 && \
          cat <&3 | grep -q 'UP'; do
        echo "Waiting for Keycloak to be ready..."
        sleep 5
    done
    echo "Keycloak is ready!"
}

# Function to get admin token
set_admin_credentials() {
    echo "Setting admin credentials..."
    /opt/keycloak/bin/kcadm.sh config credentials \
        --server http://localhost:8080/auth \
        --realm master \
        --user temp-admin \
        --password $KEYCLOAK_TEMP_ADMIN_PASSWORD \
        --client admin-cli
    echo "Admin credentials set!"
}

# Import realm settings from file and apply to master realm
configure_master_realm() {
    echo "Configuring master realm with idapt settings..."
    
    # Check if realm export file exists
    if [ ! -f "/realm-export.json" ]; then
        echo "Error: realm-export.json file not found!"
        exit 1
    fi

    # Update master realm with the configuration
    /opt/keycloak/bin/kcadm.sh update realms/master -f /realm-export.json -r master
    
    echo "Master realm configured!"
}

# Configure SMTP settings
configure_admin_smtp() {
    echo "Configuring SMTP settings for master realm..."
    /opt/keycloak/bin/kcadm.sh update realms/master \
        -s "smtpServer.host=$SMTP_ADDRESS" \
        -s "smtpServer.port=$SMTP_PORT" \
        -s "smtpServer.fromDisplayName=idapt" \
        -s "smtpServer.from=$SMTP_USERNAME" \
        -s "smtpServer.auth=true" \
        -s "smtpServer.ssl=$SMTP_SSL" \
        -s "smtpServer.starttls=$SMTP_STARTTLS" \
        -s "smtpServer.user=$SMTP_USERNAME" \
        -s "smtpServer.password=$SMTP_PASSWORD"
    echo "SMTP settings configured for master realm!"
}

# Create clients
create_clients() {
    echo "Creating backend client..."
    # Create backend client
    BACKEND_CLIENT_ID=$(/opt/keycloak/bin/kcadm.sh create clients -r master \
        -s clientId=idapt-backend \
        -s name=idapt-backend \
        -s enabled=true \
        -s publicClient=false \
        -s clientAuthenticatorType=client-secret \
        -s serviceAccountsEnabled=true \
        -s directAccessGrantsEnabled=true \
        -s authorizationServicesEnabled=true \
        -s protocol=openid-connect \
        -s 'redirectUris=["*"]' \
        -i)
    
    echo "Backend client created!"

    # Get and save backend client secret
    echo "Getting backend client secret..."
    COMMAND_OUTPUT=$(/opt/keycloak/bin/kcadm.sh get clients/$BACKEND_CLIENT_ID/client-secret -r master)
    BACKEND_SECRET=$(echo "$COMMAND_OUTPUT" | sed -n 's/.*"value" : "\([^"]*\)".*/\1/p')
    echo -n "$BACKEND_SECRET" > /keycloak_backend_client_secret/BACKEND_CLIENT_SECRET
    echo "Backend client secret saved!"

    echo "Creating OAuth2 proxy client..."
    # Create OAuth2 proxy client
    OAUTH2_CLIENT_ID=$(/opt/keycloak/bin/kcadm.sh create clients -r master \
        -s clientId=idapt-oauth2-proxy \
        -s enabled=true \
        -s publicClient=false \
        -s clientAuthenticatorType=client-secret \
        -s 'redirectUris=["*"]' \
        -s protocol=openid-connect \
        -s 'webOrigins=["*"]' \
        -i)
    echo "OAuth2 proxy client created!"
    
    echo "Getting OAuth2 proxy client secret..."
    # Get and save OAuth2 proxy client secret
    COMMAND_OUTPUT=$(/opt/keycloak/bin/kcadm.sh get clients/$OAUTH2_CLIENT_ID/client-secret -r master)
    OAUTH2_SECRET=$(echo "$COMMAND_OUTPUT" | sed -n 's/.*"value" : "\([^"]*\)".*/\1/p')
    echo -n "$OAUTH2_SECRET" > /keycloak_oauth2_client_secret/OAUTH2_PROXY_CLIENT_SECRET
    echo "OAuth2 proxy client secret saved!"
}

# Create new admin user account
create_admin_user() {
    echo "Creating new admin account..."
    if [ "$DEV_SET_INITIAL_KEYCLOAK_ADMIN_PASSWORD" = "true" ]; then
        echo "Creating admin account in dev mode without required actions..."
        NEW_ADMIN_ID=$(/opt/keycloak/bin/kcadm.sh create users -r master \
            -s email=$KEYCLOAK_USER_EMAIL \
            -s enabled=true \
            -s emailVerified=true \
            -i)
    else
        echo "Creating admin account with required password update action..."
        NEW_ADMIN_ID=$(/opt/keycloak/bin/kcadm.sh create users -r master \
            -s email=$KEYCLOAK_USER_EMAIL \
            -s enabled=true \
            -s emailVerified=true \
            -s requiredActions='["UPDATE_PASSWORD", "CONFIGURE_OTP"]' \
            -i)
    fi
    echo "New admin user created"
}

# Set temporary password for new admin
set_admin_temp_password() {
    if [ "$DEV_SET_INITIAL_KEYCLOAK_ADMIN_PASSWORD" = "true" ]; then
        ADMIN_PASSWORD="$DEV_INITIAL_KEYCLOAK_ADMIN_PASSWORD"
        echo "Using provided dev admin password"
    else
        # Generate a strong random password with:
        # - 64 characters
        # - Special characters
        # - Numbers
        # - Uppercase letters
        # - Lowercase letters
        # While the password do not match the password policy, generate a new one, it needs to be 64 characters long, with special characters, numbers, uppercase and lowercase letters
        while ! echo "$ADMIN_PASSWORD" | grep -qE '^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+-=])[A-Za-z\d!@#$%^&*()_+-=]{64}$'; do
            ADMIN_PASSWORD=$(tr -dc 'A-Za-z0-9!@#$%^&*()_+-=' < /dev/urandom | head -c 64)
        done
    fi

    # Set the temporary password for the new admin
    echo "Setting password for new admin..."
    echo "Admin password: $ADMIN_PASSWORD"

    if [ "$DEV_SET_INITIAL_KEYCLOAK_ADMIN_PASSWORD" = "true" ]; then
        /opt/keycloak/bin/kcadm.sh set-password -r master \
            --userid $NEW_ADMIN_ID \
            -p "$ADMIN_PASSWORD"
    else
        /opt/keycloak/bin/kcadm.sh set-password -r master \
            --userid $NEW_ADMIN_ID \
            --temporary \
            -p "$ADMIN_PASSWORD"
    fi
}

# Add admin role to new admin user
add_admin_role() {
    echo "Adding admin role to new admin user..."
    /opt/keycloak/bin/kcadm.sh add-roles -r master \
        --uusername $KEYCLOAK_USER_EMAIL \
        --rolename admin
}

# Delete temporary admin user
delete_temp_admin() {
    echo "Deleting temp-admin user..."
    TEMP_ADMIN_ID=$(/opt/keycloak/bin/kcadm.sh get users -r master -q username=temp-admin --fields id | grep -oP '"id"\s*:\s*"\K[^"]+')
    if [ -n "$TEMP_ADMIN_ID" ]; then
        /opt/keycloak/bin/kcadm.sh delete users/$TEMP_ADMIN_ID -r master
        echo "Temp admin user deleted successfully"
    else
        echo "Temp admin user not found - may have been already deleted"
    fi
}

# Main execution
wait_for_keycloak
set_admin_credentials
configure_master_realm
configure_admin_smtp
create_clients
create_admin_user
set_admin_temp_password
add_admin_role
delete_temp_admin