"""
Simple CLI to init DB and run a demo.
"""

import argparse
from datetime import datetime, timedelta
from .reservation_system.db_setup import init_db, SessionLocal
from .reservation_system.db_setup import seed_large
from .reservation_system.service import ReservationService
from .reservation_system.models import Customer  # import directly
from datetime import date as _date


def cmd_init(args):
    """Initialize the database, optionally dropping existing tables."""
    init_db(drop_first=args.drop)
    # optionally seed a larger dataset
    if getattr(args, 'seed_large', False):
        session = SessionLocal()
        seed_large(session)
        session.close()
    print("✅ Database initialized.")


def cmd_demo(args):
    """Run a simple reservation demo."""
    session = SessionLocal()
    svc = ReservationService(session)

    # pick first customer
    c = session.query(Customer).first()
    if not c:
        print("❌ No customer found in DB. Please run 'init-db' first.")
        session.close()
        return

    # Define reservation slots (start earlier so multiple 2-hour slots fit operating hours)
    start = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)

    print(f"🎉 Demo: making reservations for {c.name}")
    try:
        # Reservation 1
        r1, s1 = svc.make_reservation(c.id, start, 2, notes="Birthday")
        print(f"Reservation 1 -> Status: {s1}, ID: {r1.id}")

        # Reservation 2 (later slot)
        r2, s2 = svc.make_reservation(c.id, start + timedelta(hours=2), 5, notes="Anniversary")
        print(f"Reservation 2 -> Status: {s2}, ID: {r2.id}")

    except Exception as e:
        print("❌ Demo error:", e)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Restaurant Reservation CLI")
    sub = parser.add_subparsers()

    # init-db command
    p1 = sub.add_parser("init-db", help="Initialize the database")
    p1.add_argument("--drop", action="store_true", help="Drop existing tables first")
    p1.add_argument("--seed-large", action="store_true", dest="seed_large", help="Seed a larger dataset (10-20 entries)")
    p1.set_defaults(func=cmd_init)

    # demo command
    p2 = sub.add_parser("demo", help="Run reservation demo")
    p2.set_defaults(func=cmd_demo)

    # report command
    p3 = sub.add_parser("report", help="Generate daily reservation report")
    p3.add_argument("--date", type=str, help="Date (YYYY-MM-DD). Defaults to today.")
    p3.set_defaults(func=lambda args: cmd_report(args))

    # list-tables
    p4 = sub.add_parser("list-tables", help="List tables and their status")
    p4.set_defaults(func=lambda args: cmd_list_tables(args))

    # set-maintenance
    p5 = sub.add_parser("set-maintenance", help="Set a table active/inactive")
    p5.add_argument("table_id", type=int)
    p5.add_argument("--active", action="store_true", help="Mark table active (clear maintenance)")
    p5.add_argument("--inactive", action="store_true", help="Mark table inactive (maintenance)")
    p5.set_defaults(func=lambda args: cmd_set_maintenance(args))

    # parse args and execute
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


def cmd_report(args):
    session = SessionLocal()
    svc = ReservationService(session)
    if getattr(args, 'date', None):
        d = _date.fromisoformat(args.date)
    else:
        d = _date.today()
    report = svc.generate_daily_report(d)
    for slot in report:
        print(f"Slot: {slot['slot_start']} - {slot['slot_end']}")
        for r in slot['reservations']:
            print(f"  R{r['reservation_id']} C{r['customer_id']} size={r['party_size']} status={r['status']}")
    session.close()


def cmd_list_tables(args):
    session = SessionLocal()
    svc = ReservationService(session)
    for t in svc.list_tables():
        print(f"{t['id']}: {t['name']} cap={t['capacity']} loc={t['location']} active={t['is_active']}")
    session.close()


def cmd_set_maintenance(args):
    session = SessionLocal()
    svc = ReservationService(session)
    active = True if args.active else (False if args.inactive else None)
    if active is None:
        print("Specify --active or --inactive")
        return
    t = svc.set_table_maintenance(args.table_id, active)
    print(f"Table {t.name} set active={t.is_active}")
    session.close()


if __name__ == "__main__":
    main()
