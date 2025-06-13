#!/bin/bash
# Start the Meeting-to-Protocol microservice

# Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Make sure directories exist
mkdir -p job_data uploads logs

# Start the service with Gunicorn for production
if [ "$NODE_ENV" = "production" ]; then
    echo "Starting in production mode with Gunicorn"
    gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
else
    echo "Starting in development mode"
    python app.py
fi