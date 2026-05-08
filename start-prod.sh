#!/bin/bash

# Production startup script

echo "Starting AI Agent Backend in production mode..."

# Set production environment
export ENVIRONMENT=production

# Run database migrations if needed
# python -m app.utils.migrate_db

# Start the application with production settings
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --log-level info \
    --no-access-log
