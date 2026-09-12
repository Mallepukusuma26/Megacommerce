"""
MegaCommerce Inventory & Multi-Warehouse Database Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Float, Integer, JSON
from sqlalchemy.orm import relationship
from database.connection import Base
from shared.enums import WarehouseZone


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    street_address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state_province = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False, default="United States")
    capacity_units = Column(Integer, nullable=False, default=100000)
    current_occupancy = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    inventory_items = relationship("InventoryItem", back_populates="warehouse", cascade="all, delete-orphan")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    zone = Column(String(50), nullable=False, default=WarehouseZone.BULK_STORAGE.value)
    bin_location = Column(String(50), nullable=True)
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    reorder_quantity = Column(Integer, nullable=False, default=50)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    warehouse = relationship("Warehouse", back_populates="inventory_items")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sku = Column(String(100), nullable=False, index=True)
    from_warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True)
    to_warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    movement_type = Column(String(50), nullable=False)  # INBOUND, OUTBOUND, TRANSFER, ADJUSTMENT
    reference_id = Column(String(100), nullable=True)  # Order ID or Transfer ID
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_fulfilled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
