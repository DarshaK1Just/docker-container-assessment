"""
Allocation & optimization logic.
- compute time slots
- find optimal table or combination
- conflict detection
"""

from datetime import datetime, timedelta
from itertools import combinations
from typing import List, Tuple

# Each reservation slot = 2 hours
SLOT_LENGTH = timedelta(hours=2)

# Default operating hours (24-hour clock). Can be overridden by service if needed.
OPEN_HOUR = 12  # 12:00 PM
CLOSE_HOUR = 22  # 10:00 PM


def slot_range(start: datetime) -> Tuple[datetime, datetime]:
    """Return slot start and end for a given slot start datetime."""
    return start, start + SLOT_LENGTH


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Check if two time ranges overlap."""
    return not (a_end <= b_start or b_end <= a_start)


def find_combinations_for_party(tables: List[dict], party_size: int, max_tables_to_combine: int = 3) -> List[int]:
    """
    Find best combination(s) of tables that meet or exceed party_size.
    tables: list of dicts with 'id' and 'capacity'
    returns combination list (table ids) minimizing waste (total_capacity - party_size)
    """
    best_combo = None
    best_waste = None

    # Try single tables first, then combinations up to max_tables_to_combine
    for r in range(1, max_tables_to_combine + 1):
        for combo in combinations(tables, r):
            cap = sum(t['capacity'] for t in combo)
            if cap >= party_size:
                waste = cap - party_size
                if best_waste is None or waste < best_waste:
                    best_combo = combo
                    best_waste = waste
        # If an exact or best combo found, stop early
        if best_combo:
            break

    if best_combo:
        return [t['id'] for t in best_combo]
    return []


def compute_availability(session, slot_start: datetime) -> List[dict]:
    """
    Return list of available tables (dict with id, capacity, name) for a given slot start.
    Only tables with is_active==True and not allocated in overlapping reservations are included.
    """
    from .models import Table, Allocation, Reservation

    slot_end = slot_start + SLOT_LENGTH

    # --- Step 1: Get all active tables ---
    tables = session.query(Table).filter(Table.is_active == True).all()
    available_tables = [{'id': t.id, 'capacity': t.capacity, 'name': t.name} for t in tables]

    # --- Step 2: Get all allocations with overlapping reservations ---
    allocations = (
        session.query(Allocation)
        .join(Reservation)
        .filter(Reservation.status == 'CONFIRMED')
        .all()
    )

    # --- Step 3: Remove tables that are booked in overlapping slots ---
    booked_table_ids = set()
    for alloc in allocations:
        res = alloc.reservation
        if overlaps(res.slot_start, res.slot_end, slot_start, slot_end):
            booked_table_ids.add(alloc.table_id)

    available = [t for t in available_tables if t['id'] not in booked_table_ids]
    return available


def is_within_operating_hours(slot_start: datetime, open_hour: int = OPEN_HOUR, close_hour: int = CLOSE_HOUR) -> bool:
    """Return True if the slot_start falls within operating hours (slot must start on or after open_hour and end on or before close_hour)."""
    slot_end = slot_start + SLOT_LENGTH
    # compare by hour only (assumes slots align to the day)
    return (open_hour <= slot_start.hour) and (slot_end.hour <= close_hour)
