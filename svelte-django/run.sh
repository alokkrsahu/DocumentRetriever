#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# Kill processes on default Svelte and Django ports
echo "Killing existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null  # Django default port
lsof -ti:8080 | xargs kill -9 2>/dev/null  # Svelte default port

# Remove log files
rm "$SCRIPT_DIR/frontend/fileupload-frontend/svelte_log.txt"
rm "$SCRIPT_DIR/backend/fileupload_project/django_log.txt"

# Launch Svelte
echo "Launching Svelte..."
cd "$SCRIPT_DIR/frontend/fileupload-frontend"
npm run dev:custom > svelte_log.txt 2>&1 &

# Wait for Svelte to start
sleep 5

# Launch Django
echo "Launching Django..."
cd "$SCRIPT_DIR/backend/fileupload_project"
python manage.py runserver 8000 > django_log.txt 2>&1 &

echo "Both processes launched. Check svelte_log.txt and django_log.txt for output."

