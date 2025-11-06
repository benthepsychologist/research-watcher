#!/bin/bash
set -e

# Load environment variables if .env exists
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source .venv/bin/activate

# Run Flask development server
echo "Starting Research Watcher development server..."
echo "Access at: http://localhost:${PORT:-3000}"
python -u -m flask --app main run --debug --host=0.0.0.0 --port=${PORT:-3000}