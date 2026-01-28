from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Column, ForeignKey, Table, Float, Integer
from datetime import date

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Junction table for many-to-many relationship between tickets and mechanics
ticket_mechanic = Table(
    'ticket_mechanic',
    Base.metadata,
    Column('ticket_id', Integer, ForeignKey('service_tickets.id'), primary_key=True),
    Column('mechanic_id', Integer, ForeignKey('mechanics.id'), primary_key=True)
)

# Junction table for many-to-many relationship between tickets and inventory
ticket_inventory = Table(
    'ticket_inventory',
    Base.metadata,
    Column('ticket_id', Integer, ForeignKey('service_tickets.id'), primary_key=True),
    Column('inventory_id', Integer, ForeignKey('inventory.id'), primary_key=True)
)

# Customers table
class Customers(Base):
    __tablename__ = 'customers'
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(350), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationship: one customer can have many service tickets
    service_tickets: Mapped[list["ServiceTickets"]] = relationship(back_populates="customer")

# Service Tickets table
class ServiceTickets(Base):
    __tablename__ = 'service_tickets'
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), nullable=False)
    service_desc: Mapped[str] = mapped_column(String(1000), nullable=False)
    VIN: Mapped[str] = mapped_column(String(17), nullable=False)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    customer: Mapped["Customers"] = relationship(back_populates="service_tickets")
    mechanics: Mapped[list["Mechanics"]] = relationship(secondary=ticket_mechanic, back_populates="service_tickets")
    inventory_items: Mapped[list["Inventory"]] = relationship(secondary=ticket_inventory, back_populates="service_tickets")
    parts: Mapped[list["Parts"]] = relationship(back_populates="service_ticket")

# Mechanics table
class Mechanics(Base):
    __tablename__ = 'mechanics'
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(350), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationship: one mechanic can work on many service tickets
    service_tickets: Mapped[list["ServiceTickets"]] = relationship(secondary=ticket_mechanic, back_populates="mechanics")

# Inventory table (Part Description)
class Inventory(Base):
    __tablename__ = 'inventory'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    service_tickets: Mapped[list["ServiceTickets"]] = relationship(secondary=ticket_inventory, back_populates="inventory_items")
    parts: Mapped[list["Parts"]] = relationship(back_populates="inventory_description", cascade="all, delete-orphan", passive_deletes=True)

# Parts table (Individual parts used on tickets)
class Parts(Base):
    __tablename__ = 'parts'
    id: Mapped[int] = mapped_column(primary_key=True)
    desc_id: Mapped[int] = mapped_column(ForeignKey('inventory.id', ondelete="CASCADE"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('service_tickets.id', ondelete="SET NULL"), nullable=True)

    # Relationships
    inventory_description: Mapped["Inventory"] = relationship(back_populates="parts")
    service_ticket: Mapped["ServiceTickets"] = relationship(back_populates="parts")