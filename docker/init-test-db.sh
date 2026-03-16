#!/bin/bash
# Creates the test database alongside the main app database.
# Mounted into /docker-entrypoint-initdb.d/ so Postgres runs it on first init.
# Uses the same user/password as the main DB (from env vars set in compose.yml).

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE app_test;
    GRANT ALL PRIVILEGES ON DATABASE app_test TO $POSTGRES_USER;
EOSQL
