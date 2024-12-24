-- Create the vector extension first (as postgres superuser)

-- Create users and databases
CREATE USER "idapt-backend" WITH PASSWORD '${IDAPT_BACKEND_PASSWORD}';
CREATE USER "idapt-keycloak" WITH PASSWORD '${IDAPT_KEYCLOAK_PASSWORD}';

CREATE DATABASE "idapt-backend";
CREATE DATABASE "idapt-keycloak" with encoding 'UTF8';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE "idapt-backend" TO "idapt-backend";
GRANT ALL PRIVILEGES ON DATABASE "idapt-keycloak" TO "idapt-keycloak";

-- Connect to each database and set ownership
\c "idapt-backend"
--ALTER DATABASE "idapt-backend" OWNER TO "idapt-backend";
ALTER SCHEMA public OWNER TO "idapt-backend";
CREATE EXTENSION IF NOT EXISTS vector;


\c "idapt-keycloak"
--ALTER DATABASE "idapt-keycloak" OWNER TO "idapt-keycloak";
ALTER SCHEMA public OWNER TO "idapt-keycloak"; 