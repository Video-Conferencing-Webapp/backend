#!/bin/bash
set -e

# Apply database migrations
echo "Backend entrypoint: Applying database migrations..."
alembic upgrade head

# Then exec the container's main process (what's_set as CMD)
echo "Backend entrypoint: Starting Uvicorn server..."
exec "$@"
