"""
MegaCommerce Promotions Core — Coupon Evaluation & Stackability Matrix
"""

import datetime
from typing import Dict, Any, List, Optional
from shared.enums import CouponType


class CouponEvaluatorEngine:
    """Evaluates promotional coupons, applicability constraints, and max discounts."""

    @staticmethod
    def evaluate_coupon(
        coupon_data: Dict[str, Any],
        cart_subtotal: float,
        cart_categories: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Input format:
        coupon_data = {
            'code': 'SAVE20', 'type': 'PERCENTAGE', 'value': 20.0,
            'min_subtotal': 100.0, 'max_discount': 50.0, 'is_active': True,
            'expiry_date': datetime, 'allowed_categories': []
        }
        """
        code = coupon_data.get("code", "UNKNOWN")
        if not coupon_data.get("is_active", False):
            return {"is_valid": False, "reason": f"Coupon '{code}' is inactive.", "discount_amount": 0.0}

        expiry = coupon_data.get("expiry_date")
        if expiry and datetime.datetime.utcnow() > expiry:
            return {"is_valid": False, "reason": f"Coupon '{code}' has expired.", "discount_amount": 0.0}

        min_val = coupon_data.get("min_subtotal", 0.0)
        if cart_subtotal < min_val:
            return {"is_valid": False, "reason": f"Cart subtotal (${cart_subtotal:.2f}) does not meet minimum threshold (${min_val:.2f}).", "discount_amount": 0.0}

        c_type = coupon_data.get("type", CouponType.PERCENTAGE.value)
        val = coupon_data.get("value", 0.0)

        if c_type == CouponType.PERCENTAGE.value or c_type == "PERCENTAGE":
            discount = cart_subtotal * (val / 100.0)
        elif c_type == CouponType.FIXED_AMOUNT.value or c_type == "FIXED_AMOUNT":
            discount = val
        elif c_type == CouponType.FREE_SHIPPING.value or c_type == "FREE_SHIPPING":
            discount = 15.00  # Default shipping fee offset
        else:
            discount = 0.0

        max_disc = coupon_data.get("max_discount")
        if max_disc and discount > max_disc:
            discount = max_disc

        discount = round(min(discount, cart_subtotal), 2)

        return {
            "is_valid": True,
            "coupon_code": code,
            "discount_amount": discount,
            "net_subtotal": round(cart_subtotal - discount, 2)
        }
