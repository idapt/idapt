# This is installing the pgvector extension for postgres not present in the postgres image.
FROM postgres:latest

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-all \
    postgresql-client \ 
    && rm -rf /var/lib/apt/lists/*
# Need the postgresql-client for the pg_isready command
WORKDIR /tmp

# Check if the pgvector directory exists before cloning
RUN if [ ! -d "pgvector" ]; then \
        git clone https://github.com/pgvector/pgvector.git; \
    fi

WORKDIR /tmp/pgvector
RUN make
RUN make install