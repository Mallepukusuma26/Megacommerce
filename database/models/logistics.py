"""
MegaCommerce Delivery Logistics, Returns, & Refund Simulator Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Float, Integer, JSON
from sqlalchemy.orm import relationship
from database.connection import Base
from shared.enums import ShipmentStatus, ReturnStatus, ReturnReason, PaymentStatus


def generate_uuid() -> str:
    return str(uuid.uuid4())


class DeliveryAgent(Base):
    __tablename__ = "delivery_agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    vehicle_type = Column(String(50), nullable=False, default="VAN")
    license_plate = Column(String(50), nullable=True)
    current_city = Column(String(100), nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    active_shipments_count = Column(Integer, default=0, nullable=False)
    rating_average = Column(Float, default=5.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    shipments = relationship("Shipment", back_populates="delivery_agent")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    delivery_agent_id = Column(String(36), ForeignKey("delivery_agents.id"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    tracking_number = Column(String(100), unique=True, nullable=False, index=True)
    
    status = Column(String(50), nullable=False, default=ShipmentStatus.UNASSIGNED.value, index=True)
    estimated_delivery_date = Column(DateTime, nullable=False)
    actual_delivery_date = Column(DateTime, nullable=True)
    current_location = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="shipment")
    delivery_agent = relationship("DeliveryAgent", back_populates="shipments")
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    shipment = relationship("Shipment", back_populates="events")


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    reason = Column(String(50), nullable=False, default=ReturnReason.DEFECTIVE.value)
    details = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default=ReturnStatus.REQUESTED.value, index=True)
    refund_amount = Column(Float, nullable=False)
    inspection_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    refund_transaction = relationship("RefundTransaction", back_populates="return_request", uselist=False)


class RefundTransaction(Base):
    __tablename__ = "refund_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    return_request_id = Column(String(36), ForeignKey("return_requests.id", ondelete="CASCADE"), unique=True, nullable=False)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    refund_reference = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default=PaymentStatus.REFUNDED.value)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    return_request = relationship("ReturnRequest", back_populates="refund_transaction")
