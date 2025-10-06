import os
from datetime import datetime, timedelta, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, Table, Customer  # package-relative import

# --- Database Configuration ---
DB_URL = os.getenv('RRS_DB', 'sqlite:///reservation.db')
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)


def init_db(drop_first: bool = False):
    """
    Initialize the database, optionally dropping all existing tables first.
    Also seeds sample tables and customers if the database is empty.
    """
    if drop_first:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Open session
    session = SessionLocal()

    try:
        # --- Seed Tables ---
        if session.query(Table).count() == 0:
            tables = [
                Table(name='T1', capacity=2, location='Window'),
                Table(name='T2', capacity=2, location='Window'),
                Table(name='T3', capacity=4, location='Center'),
                Table(name='T4', capacity=4, location='Center'),
                Table(name='T5', capacity=6, location='Private'),
                Table(name='T6', capacity=8, location='Private'),
            ]
            session.add_all(tables)
            print("✅ Seeded sample tables.")

        # --- Seed Customers ---
        if session.query(Customer).count() == 0:
            customers = [
                Customer(
                    name='Darshak Kakani',
                    phone='91-99999',
                    email='darshak@example.com',
                    dietary='vegetarian',
                    preferences={'corner': True},
                ),
                Customer(
                    name='Raju Khatri',
                    phone='91-88888',
                    email='raju@example.com',
                ),
            ]
            session.add_all(customers)
            print("✅ Seeded sample customers.")

        session.commit()
        print("🎉 Database initialized successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error initializing DB: {e}")
    finally:
        session.close()


def seed_large(session, num_tables: int = 12, num_customers: int = 15):
    """Seed a larger dataset: create num_tables tables and num_customers customers and some reservations."""
    from .models import Table, Customer, Reservation
    from .allocator import SLOT_LENGTH
    import random

    # Create tables if needed (avoid name collisions)
    existing_tables = [t[0] for t in session.query(Table.name).all()]
    existing_count = len(existing_tables)
    # find highest numeric suffix for names like 'T<number>'
    max_idx = 0
    for name in existing_tables:
        if name and name.startswith('T') and name[1:].isdigit():
            try:
                n = int(name[1:])
                if n > max_idx:
                    max_idx = n
            except ValueError:
                continue

    to_create = max(0, num_tables - existing_count)
    if to_create > 0:
        tables = []
        caps = [2, 2, 4, 4, 6, 6, 8]
        for offset in range(1, to_create + 1):
            i = max_idx + offset
            cap = caps[(i - 1) % len(caps)]
            tables.append(Table(name=f'T{i}', capacity=cap, location=random.choice(['Window', 'Center', 'Private'])))
        try:
            session.add_all(tables)
            session.commit()
            print(f"✅ Seeded {to_create} tables (total {existing_count + to_create}).")
        except Exception as e:
            session.rollback()
            print(f"❌ Error seeding tables: {e}")

    # Create customers
    existing_customers = session.query(Customer).count()
    to_create_cust = max(0, num_customers - existing_customers)
    if to_create_cust > 0:
        customers = []
        for i in range(existing_customers + 1, existing_customers + to_create_cust + 1):
            customers.append(Customer(name=f'Customer{i}', phone=f'91-9{i:05d}', email=f'cust{i}@example.com'))
        try:
            session.add_all(customers)
            session.commit()
            print(f"✅ Seeded {to_create_cust} customers (total {existing_customers + to_create_cust}).")
        except Exception as e:
            session.rollback()
            print(f"❌ Error seeding customers: {e}")

    # Create some sample reservations across today's slots
    # pick a few customers and make reservations across open hours
    from .service import ReservationService
    svc = ReservationService(session)
    import datetime
    today = datetime.date.today()
    start_hour = svc.open_hour
    # make reservations for several slots
    for hour in range(start_hour, svc.close_hour, int(SLOT_LENGTH.seconds / 3600)):
        slot = datetime.datetime.combine(today, datetime.time()).replace(hour=hour)
        # pick 3 random customers for this slot
        custs = session.query(Customer).all()
        if not custs:
            continue
        picks = random.sample(custs, min(3, len(custs)))
        for c in picks:
            try:
                svc.make_reservation(c.id, slot, random.choice([2, 2, 4, 4, 6]))
            except Exception:
                # ignore if waitlisted or overbook
                continue

    session.commit()
    print("🎉 Large seed complete.")


if __name__ == '__main__':
    init_db(drop_first=True)
    print(f"📦 DB initialized with sample data at {DB_URL}")
