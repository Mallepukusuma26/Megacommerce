"""
MegaCommerce Returns & Local Refund Simulation Service
"""

import uuid
import datetime
import random
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models.logistics import ReturnRequest, RefundTransaction
from database.models.order import Order, OrderHistory, PaymentTransaction
from database.models.user import AuditLog
from shared.enums import ReturnStatus, ReturnReason, OrderStatus, PaymentStatus, AuditAction
from shared.exceptions import ResourceNotFoundError, InvalidStateTransitionError


def generate_refund_ref() -> str:
    return f"REF-SIM-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


class ReturnsRefundsService:
    """Core service for managing customer return requests and local refund processing."""

    def __init__(self, db: Session):
        self.db = db

    def create_return_request(self, customer_id: str, order_id: str, reason: ReturnReason, details: str) -> ReturnRequest:
        """Customer submits return request for delivered order."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundError("Order", order_id)

        if order.customer_id != customer_id:
            raise ResourceNotFoundError("Order", order_id)

        return_req = ReturnRequest(
            order_id=order_id,
            customer_id=customer_id,
            reason=reason.value if isinstance(reason, ReturnReason) else str(reason),
            details=details,
            status=ReturnStatus.REQUESTED.value,
            refund_amount=order.total_amount
        )
        self.db.add(return_req)

        # Update Order Status
        old_status = order.order_status
        order.order_status = OrderStatus.RETURN_REQUESTED.value

        hist = OrderHistory(
            order_id=order.id,
            from_status=old_status,
            to_status=OrderStatus.RETURN_REQUESTED.value,
            notes=f"Return requested. Reason: {reason.value}"
        )
        self.db.add(hist)
        self.db.commit()
        return return_req

    def process_return_inspection(self, return_request_id: str, passed_inspection: bool, notes: str) -> ReturnRequest:
        """Warehouse inspection of returned merchandise."""
        req = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_request_id).first()
        if not req:
            raise ResourceNotFoundError("ReturnRequest", return_request_id)

        if passed_inspection:
            req.status = ReturnStatus.INSPECTED_PASSED.value
            req.inspection_notes = f"PASSED: {notes}"
            # Automatically trigger refund
            self.execute_refund_simulation(req.id)
        else:
            req.status = ReturnStatus.INSPECTED_FAILED.value
            req.inspection_notes = f"REJECTED: {notes}"

        self.db.commit()
        return req

    def execute_refund_simulation(self, return_request_id: str) -> RefundTransaction:
        """Local refund simulator executing credit back to customer."""
        req = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_request_id).first()
        if not req:
            raise ResourceNotFoundError("ReturnRequest", return_request_id)

        refund_ref = generate_refund_ref()

        refund_tx = RefundTransaction(
            return_request_id=req.id,
            order_id=req.order_id,
            refund_reference=refund_ref,
            amount=req.refund_amount,
            status=PaymentStatus.REFUNDED.value
        )
        self.db.add(refund_tx)

        req.status = ReturnStatus.REFUNDED.value
        order = self.db.query(Order).filter(Order.id == req.order_id).first()
        if order:
            order.order_status = OrderStatus.REFUNDED.value
            order.payment_status = PaymentStatus.REFUNDED.value

        # Audit Log
        audit = AuditLog(
            user_id=req.customer_id,
            action=AuditAction.REFUND_PROCESSED.value,
            entity_name="RefundTransaction",
            entity_id=refund_tx.id,
            details={"refund_reference": refund_ref, "amount": req.refund_amount}
        )
        self.db.add(audit)
        self.db.commit()
        return refund_tx
