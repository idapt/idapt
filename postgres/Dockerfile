# Use the official Postgres image as a base image
FROM postgres:latest

# Install the build dependencies
USER root

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-all \
    postgresql-client \
    gettext-base \
    && rm -rf /var/apt/lists/*

# Clone, build, and install the pgvector extension #TODO : Use a dedicated pgvector image for this ?
WORKDIR /tmp
RUN rm -rf pgvector && \
    git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install

# Create initialization script to enable the extension
RUN echo 'CREATE EXTENSION IF NOT EXISTS vector;' > /docker-entrypoint-initdb.d/init-vector.sql

# Create and set permissions for directories
RUN mkdir -p /docker-entrypoint-initdb.d \
    /postgres_admin_secrets \
    /postgres_backend_secrets \
    /postgres_keycloak_secrets \
    && chmod 777 /docker-entrypoint-initdb.d \
    /postgres_admin_secrets \
    /postgres_backend_secrets \
    /postgres_keycloak_secrets

# Copy initialization scripts
COPY init-users-db.sql /docker-entrypoint-initdb.d/init-users-db.sql.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch back to postgres user for security
USER postgres

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
