from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Table(Base):
    __tablename__ = 'tables'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)  # False if under maintenance
    notes = Column(Text, nullable=True)

    # Relationship
    allocations = relationship('Allocation', back_populates='table')

    def __repr__(self):
        return f"<Table {self.name} (Capacity: {self.capacity})>"


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    dietary = Column(String, nullable=True)
    preferences = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationship
    reservations = relationship('Reservation', back_populates='customer')

    def __repr__(self):
        return f"<Customer {self.name}>"


class Reservation(Base):
    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    slot_start = Column(DateTime, nullable=False)  # Slot start time
    slot_end = Column(DateTime, nullable=False)    # Slot end time
    party_size = Column(Integer, nullable=False)
    status = Column(String, default='CONFIRMED')   # CONFIRMED, CANCELLED, WAITLIST
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    # Relationships
    customer = relationship('Customer', back_populates='reservations')
    allocations = relationship('Allocation', back_populates='reservation')

    def __repr__(self):
        return f"<Reservation {self.id} - Customer {self.customer_id} ({self.status})>"


class Allocation(Base):
    """
    Allocation links a reservation to a specific table (for multi-table setups)
    """
    __tablename__ = 'allocations'

    id = Column(Integer, primary_key=True)
    reservation_id = Column(Integer, ForeignKey('reservations.id'), nullable=False)
    table_id = Column(Integer, ForeignKey('tables.id'), nullable=False)

    # Relationships
    reservation = relationship('Reservation', back_populates='allocations')
    table = relationship('Table', back_populates='allocations')

    def __repr__(self):
        return f"<Allocation R{self.reservation_id}:T{self.table_id}>"
