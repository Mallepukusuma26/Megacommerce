"""
MegaCommerce Internal Payment Simulator Engine
Zero External API Key Compliance Architecture
Supports Simulated Card, UPI, Wallet, NetBanking, and COD Payments
"""

import uuid
import datetime
import random
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.order import Order, PaymentTransaction, OrderHistory
from database.models.user import AuditLog
from shared.enums import PaymentStatus, PaymentMethod, OrderStatus, AuditAction
from shared.exceptions import PaymentSimulationError, ResourceNotFoundError
from shared.dtos import PaymentSimulateRequest, PaymentSimulateResponse
from config.settings import settings


def generate_tx_ref() -> str:
    return f"TXN-SIM-{datetime.datetime.utcnow().strftime('%Y%m%m%H%M%S')}-{random.randint(1000, 9999)}"


class PaymentSimulatorEngine:
    """Internal Local Payment Simulator Gateway."""

    def __init__(self, db: Session):
        self.db = db

    def process_payment(self, req: PaymentSimulateRequest) -> PaymentSimulateResponse:
        """Simulates payment gateway transaction lifecycle."""
        order = self.db.query(Order).filter(Order.id == req.order_id).first()
        if not order:
            raise ResourceNotFoundError("Order", req.order_id)

        tx_ref = generate_tx_ref()

        # Determine success vs failure simulation
        should_fail = req.simulate_failure
        if not should_fail and settings.simulators.PAYMENT_GATEWAY_SUCCESS_RATE < 1.0:
            # Deterministic simulation based on amount
            if req.amount > 50000.0:
                should_fail = True

        status = PaymentStatus.FAILED.value if should_fail else PaymentStatus.SUCCESS.value
        msg = "Payment simulation failed (simulated decline)." if should_fail else "Payment simulation completed successfully."

        gateway_log = {
            "simulator": "MegaCommerce-Local-Gateway-v1.0",
            "method": req.payment_method,
            "amount": req.amount,
            "currency": settings.simulators.DEFAULT_CURRENCY,
            "status": status,
            "card_last4": req.card_number_last4 if req.payment_method == PaymentMethod.CARD_SIMULATOR else None,
            "upi_id": req.upi_id if req.payment_method == PaymentMethod.UPI_SIMULATOR else None,
            "ip_address": "127.0.0.1",
            "simulated_at": datetime.datetime.utcnow().isoformat()
        }

        # Save PaymentTransaction
        transaction = PaymentTransaction(
            order_id=order.id,
            transaction_reference=tx_ref,
            payment_method=req.payment_method,
            status=status,
            amount=req.amount,
            currency=settings.simulators.DEFAULT_CURRENCY,
            gateway_response=gateway_log
        )
        self.db.add(transaction)

        # Update Order State
        if status == PaymentStatus.SUCCESS.value:
            order.payment_status = PaymentStatus.SUCCESS.value
            old_status = order.order_status
            order.order_status = OrderStatus.CONFIRMED.value
            
            history = OrderHistory(
                order_id=order.id,
                from_status=old_status,
                to_status=OrderStatus.CONFIRMED.value,
                notes=f"Payment succeeded via {req.payment_method}. Tx: {tx_ref}"
            )
            self.db.add(history)
        else:
            order.payment_status = PaymentStatus.FAILED.value

        # Audit Log
        audit = AuditLog(
            user_id=order.customer_id,
            action=AuditAction.PAYMENT_SIMULATED.value,
            entity_name="PaymentTransaction",
            entity_id=transaction.id,
            details=gateway_log
        )
        self.db.add(audit)
        self.db.commit()

        if should_fail:
            raise PaymentSimulationError(msg, transaction_id=tx_ref)

        return PaymentSimulateResponse(
            transaction_id=tx_ref,
            order_id=order.id,
            status=status,
            payment_method=req.payment_method,
            amount=req.amount,
            timestamp=datetime.datetime.utcnow(),
            message=msg,
            gateway_audit_log=gateway_log
        )
