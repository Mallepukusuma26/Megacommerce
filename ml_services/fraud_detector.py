"""
MegaCommerce Local Fraud Detection Engine
Zero External AI API Key Compliance Architecture
Statistical Anomaly & Multi-Rule Fraud Detection Pipeline
"""

import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models.order import Order
from database.models.user import User, AuditLog
from database.models.analytics import FraudEvent
from shared.enums import FraudRiskCategory, AuditAction
from shared.dtos import FraudAssessmentResponse
from config.settings import settings


class LocalFraudDetector:
    """Local Anomaly & Statistical Rule Fraud Engine."""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_order_risk(self, order_id: str) -> FraudAssessmentResponse:
        """Evaluates fraud risk score (0.0 to 1.0) based on velocity, amount, coupon usage, and user history."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return FraudAssessmentResponse(
                order_id=order_id,
                risk_score=0.0,
                risk_category=FraudRiskCategory.LOW.value,
                flagged=False,
                risk_reasons=[],
                evaluation_timestamp=datetime.datetime.utcnow()
            )

        risk_score = 0.0
        reasons = []

        # Rule 1: High Transaction Value Threshold ($2000+)
        if order.total_amount >= 2000.0:
            risk_score += 0.35
            reasons.append(f"Unusually high transaction value (${order.total_amount:.2f}).")

        # Rule 2: Order Velocity Check (More than 3 orders placed in past 10 minutes)
        ten_mins_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
        recent_order_count = (
            self.db.query(func.count(Order.id))
            .filter(Order.customer_id == order.customer_id, Order.created_at >= ten_mins_ago)
            .scalar()
        )
        if recent_order_count >= 3:
            risk_score += 0.45
            reasons.append(f"High order velocity detected ({recent_order_count} orders in 10 minutes).")

        # Rule 3: Unusually High Coupon Discount (>50% of subtotal)
        if order.subtotal > 0 and (order.discount_amount / order.subtotal) > 0.50:
            risk_score += 0.25
            reasons.append("Abnormal promotional coupon discount percentage (>50%).")

        # Cap Risk Score to 1.0 max
        risk_score = min(1.0, round(risk_score, 2))

        # Determine Risk Category
        if risk_score >= settings.ml.FRAUD_RISK_THRESHOLD_HIGH:
            category = FraudRiskCategory.HIGH.value
        elif risk_score >= settings.ml.FRAUD_RISK_THRESHOLD_MEDIUM:
            category = FraudRiskCategory.MEDIUM.value
        else:
            category = FraudRiskCategory.LOW.value

        is_flagged = (category in [FraudRiskCategory.HIGH.value, FraudRiskCategory.CRITICAL.value])

        # Save FraudEvent
        event = FraudEvent(
            order_id=order.id,
            user_id=order.customer_id,
            risk_score=risk_score,
            risk_category=category,
            flagged=is_flagged,
            detection_reasons=reasons
        )
        self.db.add(event)

        if is_flagged:
            audit = AuditLog(
                user_id=order.customer_id,
                action=AuditAction.FRAUD_FLAGGED.value,
                entity_name="Order",
                entity_id=order.id,
                details={"risk_score": risk_score, "reasons": reasons}
            )
            self.db.add(audit)

        self.db.commit()

        return FraudAssessmentResponse(
            order_id=order.id,
            risk_score=risk_score,
            risk_category=category,
            flagged=is_flagged,
            risk_reasons=reasons,
            evaluation_timestamp=datetime.datetime.utcnow()
        )
