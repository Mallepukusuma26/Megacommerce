"""
MegaCommerce Internal Delivery & Logistics Simulator Engine
Zero External API Key Compliance Architecture
"""

import uuid
import datetime
import random
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models.logistics import DeliveryAgent, Shipment, ShipmentEvent
from database.models.order import Order, OrderHistory
from database.models.inventory import Warehouse
from database.models.user import User, AuditLog
from shared.enums import ShipmentStatus, OrderStatus, AuditAction
from shared.exceptions import ResourceNotFoundError, InvalidStateTransitionError


def generate_tracking_number() -> str:
    return f"TRK-SIM-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"


class DeliverySimulatorEngine:
    """Internal Local Shipping & Delivery Route Simulator Engine."""

    def __init__(self, db: Session):
        self.db = db

    def register_delivery_agent(self, user_id: str, city: str, vehicle_type: str = "VAN") -> DeliveryAgent:
        """Registers a delivery agent user."""
        agent = DeliveryAgent(
            user_id=user_id,
            current_city=city,
            vehicle_type=vehicle_type,
            is_available=True
        )
        self.db.add(agent)
        self.db.commit()
        return agent

    def create_shipment_for_order(self, order_id: str, warehouse_id: str) -> Shipment:
        """Creates shipment package and assigns tracking number."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundError("Order", order_id)

        tracking_num = generate_tracking_number()
        order.tracking_number = tracking_num

        est_delivery = datetime.datetime.utcnow() + datetime.timedelta(days=3)

        shipment = Shipment(
            order_id=order_id,
            warehouse_id=warehouse_id,
            tracking_number=tracking_num,
            status=ShipmentStatus.UNASSIGNED.value,
            estimated_delivery_date=est_delivery,
            current_location="Warehouse Facility"
        )
        self.db.add(shipment)
        self.db.flush()

        # Initial Event
        evt = ShipmentEvent(
            shipment_id=shipment.id,
            status=ShipmentStatus.UNASSIGNED.value,
            location="Warehouse Fulfillment Center",
            description="Shipment created and packed at warehouse."
        )
        self.db.add(evt)
        self.db.commit()
        return shipment

    def auto_assign_delivery_agent(self, shipment_id: str) -> DeliveryAgent:
        """Dispatches available agent in nearest city queue."""
        shipment = self.db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise ResourceNotFoundError("Shipment", shipment_id)

        agent = self.db.query(DeliveryAgent).filter(DeliveryAgent.is_available == True).first()
        if not agent:
            # Create default demo agent
            dummy_user = User(
                email=f"agent_{random.randint(100,999)}@megacommerce.com",
                hashed_password="hash",
                first_name="Speedy",
                last_name="Courier",
                role="DELIVERY_AGENT"
            )
            self.db.add(dummy_user)
            self.db.flush()
            agent = DeliveryAgent(user_id=dummy_user.id, current_city="Seattle", vehicle_type="EV-VAN")
            self.db.add(agent)
            self.db.flush()

        shipment.delivery_agent_id = agent.id
        shipment.status = ShipmentStatus.ASSIGNED.value
        agent.active_shipments_count += 1

        evt = ShipmentEvent(
            shipment_id=shipment.id,
            status=ShipmentStatus.ASSIGNED.value,
            location=f"{agent.current_city} Hub",
            description=f"Assigned to delivery agent {agent.id[:6]}."
        )
        self.db.add(evt)
        self.db.commit()
        return agent

    def update_shipment_status(self, shipment_id: str, new_status: ShipmentStatus, location: str, notes: str) -> Shipment:
        """Advances shipment state through route events (IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED)."""
        shipment = self.db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise ResourceNotFoundError("Shipment", shipment_id)

        old_status = shipment.status
        shipment.status = new_status.value if isinstance(new_status, ShipmentStatus) else str(new_status)
        shipment.current_location = location

        if new_status == ShipmentStatus.DELIVERED or str(new_status) == ShipmentStatus.DELIVERED.value:
            shipment.actual_delivery_date = datetime.datetime.utcnow()
            # Update root order status to DELIVERED
            order = shipment.order
            if order:
                order.order_status = OrderStatus.DELIVERED.value
                hist = OrderHistory(
                    order_id=order.id,
                    from_status=old_status,
                    to_status=OrderStatus.DELIVERED.value,
                    notes=f"Shipment delivered at {location}. Notes: {notes}"
                )
                self.db.add(hist)

        evt = ShipmentEvent(
            shipment_id=shipment.id,
            status=shipment.status,
            location=location,
            description=notes
        )
        self.db.add(evt)
        self.db.commit()
        return shipment
