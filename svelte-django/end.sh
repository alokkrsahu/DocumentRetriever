lsof -ti:8000 | xargs kill -9 2>/dev/null  # Django default port
lsof -ti:8080 | xargs kill -9 2>/dev/null  # Svelte default port
