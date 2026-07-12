#!/bin/sh

set -e

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."

until nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"; do
    sleep 1
done

echo "PostgreSQL is available."

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head
fi

exec "$@"