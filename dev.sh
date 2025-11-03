#!/bin/bash

set -e

case "$1" in
  start)
    echo "Starting development environment..."
    docker compose up -d
    echo "Watching logs (Ctrl+C to exit)..."
    docker compose logs -f
    ;;
  stop)
    echo "Stopping development environment..."
    docker compose down
    ;;
  logs)
    echo "Showing logs (Ctrl+C to exit)..."
    docker compose logs -f
    ;;
  rebuild)
    echo "Rebuilding with new dependencies..."
    docker compose up --build -d
    ;;
  shell)
    echo "Opening shell in container..."
    docker compose exec app bash
    ;;
  *)
    echo "Usage: $0 {start|stop|logs|rebuild|shell}"
    echo ""
    echo "  start    - Start the development environment"
    echo "  stop     - Stop the development environment"
    echo "  logs     - Show and follow logs"
    echo "  rebuild  - Rebuild containers (after dependency changes)"
    echo "  shell    - Open a shell in the running container"
    ;;
esac