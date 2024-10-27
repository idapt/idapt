#!/bin/sh

set -e

until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 0.2
done

>&2 echo "Postgres is up - executing command"
exec "$@"