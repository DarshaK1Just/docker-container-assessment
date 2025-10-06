# Docker Container Assessment

This repository contains a small demo stack and a restaurant reservation system used for evaluation and exercises.

Contents

- `docker-compose.yml` — Compose stack (nginx, web, redis)
- `web/` — Flask backend and Docker setup for the web service
- `nginx/` — Nginx config and static content
- `restaurant-reservation-system/` — Python package implementing a reservation system, CLI, and tests

Quick goals

- Run the compose stack locally (dev).
- Use the reservation CLI to init DB, seed demo data, run a demo and generate reports.
- Explore and run unit tests for allocator and conflict logic.

Prerequisites

- Docker & Docker Compose (or Docker Desktop on Windows)
- Python 3.10+ (for the reservation-system CLI and tests)
- Optional: `sqlite3` CLI if you want to inspect `reservation.db` from terminal

Running the app (compose)

1. Build and start the stack:

```powershell
docker-compose build
docker-compose up -d
```

2. The `web` service listens on port 5000 (proxied by `nginx` in the compose stack). Example endpoints are under `/api/` (health, guestbook, docker controls if enabled).

Docker SDK notes and security

- The `web` service contains optional endpoints that use the Docker Python SDK to list/start/stop containers. For the SDK to connect to the host Docker daemon the container must have access to the Docker socket. In this repo the `docker-compose.yml` mounts `/var/run/docker.sock` into the `web` service on Unix hosts.
- IMPORTANT: mounting the Docker socket gives the container full control of the Docker daemon on the host — treat this as a privileged operation and do not enable in untrusted environments. Use `DOCKER_API_TOKEN` for minimal auth on endpoints and never commit secrets to the repo.
- Windows users: Docker Desktop uses a named pipe and does not provide a Unix socket. If you're on Windows you can either run the `web` service from WSL/Linux, or configure Docker Desktop to expose the daemon via TCP (not recommended for production) and set `DOCKER_HOST` accordingly.

Reservation system (local CLI)
The reservation system is self-contained under `restaurant-reservation-system/` and includes a tiny CLI.

1. Create a virtual environment and install dependencies (optional but recommended):

```powershell
cd restaurant-reservation-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Initialize the DB and seed demo data:

```powershell
# simple init
python -m src.cli init-db

# init and seed larger demo (12 tables, 15 customers)
python -m src.cli init-db --drop --seed-large
```

3. Run the demo that exercises reservation creation:

```powershell
python -m src.cli demo
```

4. Useful CLI commands (from `restaurant-reservation-system`):

- `python -m src.cli list-tables` — list tables and maintenance flags
- `python -m src.cli set-maintenance <table_id> --inactive|--active` — mark a table under maintenance or active
- `python -m src.cli report [--date YYYY-MM-DD]` — generate a simple daily reservations report

Tests
Run unit tests with `pytest` from `restaurant-reservation-system`:

```powershell
cd restaurant-reservation-system
pytest -q
```

Inspecting the SQLite DB

- Use the `sqlite3` CLI or the provided small Python helper to inspect `reservation.db` (see project root). Example:

```powershell
sqlite3 -header -column reservation.db "SELECT * FROM tables;"
```

Project notes & next steps

- This project intentionally includes demonstration features (Docker control endpoints, direct socket mounting, simple token auth). Before production use you should add proper authentication, validation, rate-limiting, and avoid mounting the host socket unless required.
- TODOs in the repo include adding report unit tests, HTTP endpoints for reservation reports, and further hardening.

License & contributions

- This code is provided for assessment and learning. Feel free to open issues or PRs on GitHub.

# Docker Container Assessment

Simple compose stack demonstrating a Flask `web` service, `nginx` static/reverse-proxy, and `redis` data store.

## Overview

- `web` - Flask app exposing a small API and served by Gunicorn internally on port 5000.
- `nginx` - Reverse proxy and static file server, exposed on host port 80.
- `redis` - Redis cache used by the app to store a `visits` counter.

## Quick start (Windows)

You can run this project on Windows using Docker Desktop. There are three common ways to run the shell scripts in `scripts/`:

1. Use PowerShell and docker-compose directly (no Bash required):

```powershell
# from project root
docker-compose up -d --build
```

2. Use WSL (if installed):

```powershell
wsl bash -lc "./scripts/build.sh && ./scripts/up.sh"
```

3. Use Git Bash (if installed):

```powershell
bash ./scripts/build.sh
bash ./scripts/up.sh
```

There is a PowerShell helper `scripts/run-build.ps1` which will try to use WSL or Bash and fall back to running `docker-compose` directly.

## API endpoints

All endpoints are accessible via the nginx proxy at `http://localhost`.

- GET `/api/health` - health check (checks Redis connectivity)

  - Success: `200 OK` `{ "status": "ok" }`
  - Failure: `500` `{ "status": "unhealthy", "error": "..." }`

- GET `/api/visits` - increments and returns a visits counter stored in Redis

  - Success: `200 OK` `{ "visits": 1 }`
  - Failure: `500` `{ "visits": null, "error": "..." }`

- POST `/api/echo` - echoes back JSON posted to it

  - Request JSON body: `{ "msg": "hello" }`
  - Response: `{ "you_sent": { "msg": "hello" } }`

- Static files: `http://localhost/static/index.html`

### Guestbook - Messages (real-life example)

Add and read simple guestbook messages stored in Redis.

- GET `/api/messages` - returns recent messages (most recent first)

  - Response: `{ "messages": [ { "name": "Darshak", "message": "Hi AI", "ts": 163... }, ... ] }`

- POST `/api/messages` - add a new message
  - Request JSON: `{ "name": "Raju", "message": "Hello ML" }`
  - Success: HTTP 201 `{ "stored": { "name": "Raju", "message": "Hello ML", "ts": 163... } }`

### Docker control API (backend integration)

The `web` service now includes optional endpoints to inspect and control Docker containers (uses the Docker Python SDK).

- GET `/api/docker/containers` - list containers (query param `all=true` to include stopped)

  - Example (no token):
    ```powershell
    curl.exe -i http://localhost/api/docker/containers
    ```
  - Example (with token):
    ```powershell
    curl.exe -i -H "X-Api-Token: YOUR_TOKEN" http://localhost/api/docker/containers
    ```

- POST `/api/docker/containers/<id>/stop` - stop a container

  - Example:
    ```powershell
    curl.exe -i -X POST -H "X-Api-Token: YOUR_TOKEN" http://localhost/api/docker/containers/<id>/stop
    ```

- POST `/api/docker/containers/<id>/start` - start a container
  - Example:
    ```powershell
    curl.exe -i -X POST -H "X-Api-Token: YOUR_TOKEN" http://localhost/api/docker/containers/<id>/start
    ```

Notes:

- This exposes the host Docker daemon to the web container. In production, secure it properly (use TLS, restricted tokens, or admin-only access).
- To enable the token set `DOCKER_API_TOKEN` in the `web` container environment.

## Useful Docker commands

```powershell
# show containers
docker ps

docker-compose ps

# view logs
docker-compose logs -f web

# stop and remove
docker-compose down --volumes --remove-orphans
```

## Troubleshooting tips

- If `docker`/`docker-compose` report the daemon is not running: start Docker Desktop (or WSL2 backend) first.
- If WSL shows mount errors, consider moving repo out of OneDrive or repairing WSL with `wsl --update` and checking `dmesg` inside WSL.
- If you can’t run `.sh` scripts on PowerShell, run the commands directly (they are just docker-compose invocations) or use Git Bash.

## Pushing to GitHub

1. Create a repo at `https://github.com/DarshaK1Just/docker-container-assessment` (do not initialize with README).
2. Add the remote locally if not already:

```powershell
git remote add origin https://github.com/DarshaK1Just/docker-container-assessment.git
git push -u origin master
```

Or, configure SSH and push via SSH:

```powershell
git remote add origin git@github.com:DarshaK1Just/docker-container-assessment.git
git push -u origin master
```

## Contact / Author

- Maintainer: Darshak
- Email: darshp554@gmail.com
