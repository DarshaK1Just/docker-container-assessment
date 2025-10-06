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
