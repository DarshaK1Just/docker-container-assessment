#!/usr/bin/env bash
set -euo pipefail


# Start in detached mode
docker-compose up -d --build


# Show status
docker-compose ps