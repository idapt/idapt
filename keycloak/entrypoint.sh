#!/bin/bash

# Read the password from the shared secrets volume and store it in a local variable
KC_DB_PASSWORD=$(cat /postgres_keycloak_secrets/IDAPT_KEYCLOAK_PASSWORD)

# Check if Keycloak is already initialized
if [ ! -f "/keycloak_initialized/KEYCLOAK_INITIALIZED" ]; then

  # Generate a strong random admin password (32 bytes = 256 bits)
  KEYCLOAK_TEMP_ADMIN_PASSWORD=$(tr -dc 'A-Za-z0-9!@#$%^&*()_+-=' < /dev/urandom | head -c 64)

  # Start Keycloak in background and pass the password to the Keycloak instance
  /opt/keycloak/bin/kc.sh start \
    --optimized \
    --db-password $KC_DB_PASSWORD \
    --bootstrap-admin-password $KEYCLOAK_TEMP_ADMIN_PASSWORD \
    &
  
  # Now run the init script
  /init-keycloak.sh $KEYCLOAK_TEMP_ADMIN_PASSWORD $KEYCLOAK_USER_EMAIL

  # Create initialization flag that will persist in a volume even if the container is recreated
  touch /keycloak_initialized/KEYCLOAK_INITIALIZED
  echo "Keycloak initialization completed"

  # Wait for the Keycloak process
  wait

else

  echo "Keycloak is already initialized, skipping init script."

  # Start Keycloak
  /opt/keycloak/bin/kc.sh start \
    --optimized \
    --db-password $KC_DB_PASSWORD

fi


