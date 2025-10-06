from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import Reservation, Allocation, Customer, Table
from .allocator import SLOT_LENGTH, compute_availability, find_combinations_for_party, overlaps


class ReservationService:
    def __init__(self, session: Session, overbook_pct: float = 0.1):
        """
        Reservation service for creating, modifying, and canceling reservations.
        overbook_pct: allowed overbooking fraction (e.g. 0.1 = 10%).
        """
        self.session = session
        self.overbook_pct = overbook_pct
        # default operating hours (24h). These can be customized by caller.
        self.open_hour = 12
        self.close_hour = 22

    # -------------------------------------------------------------------------
    # CREATE RESERVATION
    # -------------------------------------------------------------------------
    def make_reservation(
        self,
        customer_id: int,
        slot_start: datetime,
        party_size: int,
        preferences: dict = None,
        notes: str = "",
    ):
        """Create new reservation if availability and capacity allow."""

        slot_end = slot_start + SLOT_LENGTH

        # Enforce operating hours
        from .allocator import is_within_operating_hours
        if not is_within_operating_hours(slot_start, self.open_hour, self.close_hour):
            raise Exception("Requested slot outside operating hours")

        # Validate customer
        customer = self.session.query(Customer).get(customer_id)
        if not customer:
            raise ValueError("Customer not found")

        # Compute availability
        avail = compute_availability(self.session, slot_start)
        total_capacity = sum(
            t.capacity for t in self.session.query(Table).filter(Table.is_active == True).all()
        )

        # Check overbooking
        confirmed_count = self._confirmed_capacity(slot_start)
        if confirmed_count + party_size > total_capacity * (1 + self.overbook_pct):
            raise Exception("Cannot accept reservation — would exceed overbooking limit")

        # Find optimal table(s)
        combo = find_combinations_for_party(avail, party_size)
        if not combo:
            # If no combo, put on waitlist
            r = Reservation(
                customer_id=customer_id,
                slot_start=slot_start,
                slot_end=slot_end,
                party_size=party_size,
                status="WAITLIST",
                notes=notes,
            )
            self.session.add(r)
            self.session.commit()
            return r, "WAITLIST"

        # Create confirmed reservation and allocations
        r = Reservation(
            customer_id=customer_id,
            slot_start=slot_start,
            slot_end=slot_end,
            party_size=party_size,
            status="CONFIRMED",
            notes=notes,
        )
        self.session.add(r)
        self.session.flush()  # get reservation ID

        for tid in combo:
            alloc = Allocation(reservation_id=r.id, table_id=tid)
            self.session.add(alloc)

        self.session.commit()
        return r, "CONFIRMED"

    # -------------------------------------------------------------------------
    # CANCEL RESERVATION
    # -------------------------------------------------------------------------
    def cancel_reservation(self, reservation_id: int):
        """Cancel an existing reservation."""
        r = self.session.query(Reservation).get(reservation_id)
        if not r:
            raise ValueError("Reservation not found")
        r.status = "CANCELLED"
        r.updated_at = datetime.utcnow()
        self.session.commit()
        return r

    # -------------------------------------------------------------------------
    # MODIFY RESERVATION
    # -------------------------------------------------------------------------
    def modify_reservation(
        self, reservation_id: int, new_slot_start: datetime = None, new_party_size: int = None
    ):
        """Modify slot or party size of an existing reservation if possible."""
        r = self.session.query(Reservation).get(reservation_id)
        if not r:
            raise ValueError("Reservation not found")

        if r.status not in ["CONFIRMED", "WAITLIST"]:
            raise Exception("Only CONFIRMED or WAITLIST reservations can be modified")

        slot_start = new_slot_start or r.slot_start
        party_size = new_party_size or r.party_size
        slot_end = slot_start + SLOT_LENGTH

        # Remove existing allocations
        self.session.query(Allocation).filter(Allocation.reservation_id == r.id).delete()

        # Try to reallocate
        avail = compute_availability(self.session, slot_start)
        combo = find_combinations_for_party(avail, party_size)

        if not combo:
            # Move to waitlist if no availability
            r.status = "WAITLIST"
            r.slot_start = slot_start
            r.slot_end = slot_end
            r.party_size = party_size
            r.updated_at = datetime.utcnow()
            self.session.commit()
            return r, "WAITLIST"

        # Update and reassign
        r.slot_start = slot_start
        r.slot_end = slot_end
        r.party_size = party_size
        r.status = "CONFIRMED"
        r.updated_at = datetime.utcnow()

        for tid in combo:
            alloc = Allocation(reservation_id=r.id, table_id=tid)
            self.session.add(alloc)

        self.session.commit()
        return r, "CONFIRMED"

    # -------------------------------------------------------------------------
    # HELPER METHOD
    # -------------------------------------------------------------------------
    def _confirmed_capacity(self, slot_start: datetime) -> int:
        """Calculate total confirmed capacity in overlapping reservations."""
        slot_end = slot_start + SLOT_LENGTH
        confirmed_res = (
            self.session.query(Reservation)
            .filter(Reservation.status == "CONFIRMED")
            .all()
        )

        total = 0
        for res in confirmed_res:
            if overlaps(res.slot_start, res.slot_end, slot_start, slot_end):
                total += res.party_size
        return total

    # -------------------------------------------------------------------------
    # REPORTS
    # -------------------------------------------------------------------------
    def generate_daily_report(self, date):
        """Generate a report for a given date (datetime.date) showing each slot and allocations."""
        from .allocator import SLOT_LENGTH

        # build slots from open_hour to close_hour in SLOT_LENGTH increments
        slots = []
        start_dt = datetime.combine(date, datetime.min.time()).replace(hour=self.open_hour)
        while start_dt.hour + SLOT_LENGTH.seconds / 3600 <= self.close_hour:
            slots.append(start_dt)
            start_dt = start_dt + SLOT_LENGTH

        report = []
        for s in slots:
            slot_end = s + SLOT_LENGTH
            # find reservations overlapping this slot
            res = (
                self.session.query(Reservation)
                .filter(Reservation.slot_start >= s)
                .filter(Reservation.slot_start < slot_end)
                .all()
            )
            allocated = []
            for r in res:
                allocated.append({
                    'reservation_id': r.id,
                    'customer_id': r.customer_id,
                    'party_size': r.party_size,
                    'status': r.status,
                })
            report.append({'slot_start': s, 'slot_end': slot_end, 'reservations': allocated})

        return report

    # -------------------------------------------------------------------------
    # Additional helpers
    # -------------------------------------------------------------------------
    def customer_history(self, customer_id: int):
        """Return past reservations for a customer (most recent first)."""
        res = (
            self.session.query(Reservation)
            .filter(Reservation.customer_id == customer_id)
            .order_by(Reservation.slot_start.desc())
            .all()
        )
        out = []
        for r in res:
            out.append({
                'id': r.id,
                'slot_start': r.slot_start,
                'slot_end': r.slot_end,
                'party_size': r.party_size,
                'status': r.status,
                'notes': r.notes,
            })
        return out

    def list_tables(self):
        """Return current table list with status."""
        tbls = self.session.query(Table).all()
        return [{'id': t.id, 'name': t.name, 'capacity': t.capacity, 'location': t.location, 'is_active': t.is_active} for t in tbls]

    def set_table_maintenance(self, table_id: int, is_active: bool):
        """Mark a table active/inactive (for maintenance)."""
        t = self.session.query(Table).get(table_id)
        if not t:
            raise ValueError('Table not found')
        t.is_active = is_active
        self.session.commit()
        return t
