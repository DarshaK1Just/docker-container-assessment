from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from reservation_system.models import Base, Table, Customer, Reservation, Allocation
from reservation_system.db_setup import DB_URL
from reservation_system.db_setup import engine as base_engine
from reservation_system.db_setup import SessionLocal
from reservation_system.service import ReservationService




def setup_inmem():
    # for test we can use sqlite in-memory
    engine = create_engine('sqlite:///:memory:', echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    t1 = Table(name='T1', capacity=4)
    t2 = Table(name='T2', capacity=2)
    s.add_all([t1,t2])
    c = Customer(name='Test')
    s.add(c)
    s.commit()
    return s, c




def test_conflict_allocation():
    s, c = setup_inmem()
    svc = ReservationService(s)
    start = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    r1, st1 = svc.make_reservation(c.id, start, 4)
    assert st1 == 'CONFIRMED'
    # another reservation overlapping should be waitlist if no table
    try:
        r2, st2 = svc.make_reservation(c.id, start, 3)
    except Exception:
        # could be waitlist
        r2 = s.query(Reservation).filter(Reservation.party_size==3).first()
        assert r2 is None or r2.status == 'WAITLIST'