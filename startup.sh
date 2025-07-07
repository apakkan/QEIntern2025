#!/bin/bash

# Setup signal handlers
trap 'kill -TERM $PID' TERM INT

echo "Starting database initialization..."
python init_db.py

echo "Installing curl..."
apt-get update && apt-get install -y curl

echo "Starting FastAPI server..."
uvicorn api_server:app --host 0.0.0.0 --port 8000 --log-level debug &
PID=$!

# Wait for any process to exit
wait $PID
# Exit with status of process that exited first
exit $?