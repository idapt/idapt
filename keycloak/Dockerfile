FROM quay.io/keycloak/keycloak:26.0.7 as builder

# Copy the config file to the builder image to build with the correct settings
COPY config/keycloak.conf /opt/keycloak/conf/keycloak.conf

WORKDIR /opt/keycloak

# Build optimized version
RUN /opt/keycloak/bin/kc.sh build

# Final image
FROM quay.io/keycloak/keycloak:26.0.7

# Copy the optimized build
COPY --from=builder /opt/keycloak/ /opt/keycloak/

# Create required directories with the correct permissions
USER root
RUN mkdir -p /keycloak_oauth2_client_secret /keycloak_backend_client_secret /keycloak_initialized && \
    chown -R keycloak:root /keycloak_oauth2_client_secret /keycloak_backend_client_secret /keycloak_initialized && \
    chmod 755 /keycloak_oauth2_client_secret /keycloak_backend_client_secret /keycloak_initialized

USER keycloak

# Copy scripts
COPY --chmod=755 entrypoint.sh /entrypoint.sh
COPY --chmod=755 init-keycloak.sh /init-keycloak.sh
COPY --chmod=755 realm-export.json /realm-export.json

ENTRYPOINT ["/entrypoint.sh"]