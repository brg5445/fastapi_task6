#!/bin/sh
set -e

echo "Applying migrations..."
alembic upgrade head

echo "Starting app..."
uvicorn main:app --host 0.0.0.0 --port 8000