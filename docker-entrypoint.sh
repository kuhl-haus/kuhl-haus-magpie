#!/bin/sh
# docker-entrypoint.sh

set -exu

if [ -z "${DATABASE_URL}" ]; then
  DATABASE_URL="none"
fi

set -exu
# Wait for database if needed (for PostgreSQL in production)
if [[ "$DATABASE_URL" == postgresql* ]]; then
  echo "Waiting for PostgreSQL to become available..."

  # Extract host and port from DATABASE_URL
  host=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
  port=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

  # Default port if not specified
  if [ -z "$port" ]; then
    port=5432
  fi

  # Wait for the database to be ready
  until nc -z $host $port; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
  done

  echo "PostgreSQL is up - continuing"
fi

# Create directory for SQLite database if needed
if [[ "$DATABASE_URL" == sqlite* ]]; then
  DB_PATH=$(echo $DATABASE_URL | sed -n 's/sqlite:\/\/\(.*\)/\1/p')
  DB_DIR=$(dirname "$DB_PATH")
  mkdir -p "$DB_DIR"
fi

# Run bootstrap command
echo "Bootstrapping application..."
python -m kuhl_haus.magpie.manage bootstrap

# Execute the command passed to the script
exec "$@"