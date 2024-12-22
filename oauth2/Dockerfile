FROM quay.io/oauth2-proxy/oauth2-proxy:v7.7.1-alpine

USER root
# Install required packages
RUN apk add --no-cache bash gettext && \
    # Create the required directories with the correct permissions
    mkdir -p /oauth2_cookie_secret /etc/oauth2-proxy && \
    chown -R nobody:nobody /oauth2_cookie_secret /etc/oauth2-proxy && \
    chmod 775 /oauth2_cookie_secret /etc/oauth2-proxy

# Copy scripts and config with correct permissions
COPY --chmod=755 entrypoint.sh /entrypoint.sh
COPY --chmod=644 config/oauth2-proxy.cfg /oauth2-proxy.cfg

USER nobody

ENTRYPOINT ["/entrypoint.sh"] 