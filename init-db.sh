#!/bin/bash
#set -e

# Create the postgres user if it doesn't exist
#psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
#    DO \$\$
#    BEGIN
#        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
#            CREATE ROLE postgres LOGIN SUPERUSER;
#        END IF;
#    END
#    \$\$;

#    CREATE USER $DATABASE_USERNAME WITH PASSWORD '$DATABASE_PASSWORD';
#    CREATE DATABASE $DATABASE_NAME;
#    GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DATABASE_USERNAME;
#EOSQL