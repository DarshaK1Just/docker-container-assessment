# Restaurant Reservation System

This folder contains a small Python-based restaurant reservation system used for demonstrations and testing. It includes a CLI, data models, allocation logic, and unit tests.

Contents

- `src/` — Python package with models, allocator, service, and CLI
- `tests/` — pytest tests for allocator and conflict logic
- `reservation.db` — (optional) default SQLite DB created after `init-db`

Quick start (recommended)

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
cd restaurant-reservation-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Initialize the database and seed demo data:

```powershell
# initialize with small sample
python -m src.cli init-db

# initialize and seed larger demo (12 tables, 15 customers)
python -m src.cli init-db --drop --seed-large
```

3. Run demo to exercise reservations:

```powershell
python -m src.cli demo
```

Useful CLI commands

- `python -m src.cli list-tables` — list tables and their maintenance status
- `python -m src.cli set-maintenance <table_id> --inactive` — mark table under maintenance
- `python -m src.cli report [--date YYYY-MM-DD]` — print daily reservation report

Run tests

```powershell
pytest -q
```

Database inspection

- Use the `sqlite3` CLI or a small Python helper to inspect `reservation.db`. Example:

```powershell
sqlite3 -header -column reservation.db "SELECT * FROM reservations ORDER BY slot_start LIMIT 50;"
```

Notes & next steps

- The allocator supports 2-hour slots and can combine tables for larger parties. Tables have an `is_active` flag to mark maintenance.
- The `web` service in the repository can talk to Docker (optional) but requires mounting the Docker socket; exercise caution with socket mounting in production.

Contributing

- If you make changes, add unit tests under `tests/` and run `pytest`.
