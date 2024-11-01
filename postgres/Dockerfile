# Use the official Postgres image as a base image
FROM postgres:latest

# Install the build dependencies
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-all \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Clone, build, and install the pgvector extension
WORKDIR /tmp
RUN rm -rf pgvector && \
    git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install

# Create initialization script to enable the extension
RUN echo 'CREATE EXTENSION IF NOT EXISTS vector;' > /docker-entrypoint-initdb.d/init-vector.sql
