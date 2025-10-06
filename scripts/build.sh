#!/usr/bin/env bash
set -euo pipefail


echo "Building images..."
docker-compose build --pull --no-cache


echo "Built successfully"