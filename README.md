# Docker Container Assessment — Production-ready example

This repository demonstrates a small production-ready containerized system:

- Flask API served by Gunicorn (service `web`)
- Redis cache (service `redis`)
- nginx serving static assets and reverse-proxying API calls (service `nginx`)

## Quick start (local)

1. Build & start containers

```bash
./scripts/build.sh
./scripts/up.sh
```
