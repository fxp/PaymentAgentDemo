#!/bin/bash
# Start all services for local development using Docker Compose.
# Requires docker and docker compose installed.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

docker compose up --build
