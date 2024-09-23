#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# Display the contents of the log files
cat "$SCRIPT_DIR/frontend/fileupload-frontend/svelte_log.txt"
cat "$SCRIPT_DIR/backend/fileupload_project/django_log.txt"

