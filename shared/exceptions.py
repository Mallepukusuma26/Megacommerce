"""
MegaCommerce Centralized Domain Exceptions & Error Hierarchy
"""

from typing import Optional, Dict, Any


class MegaCommerceException(Exception):
    """Base exception for all domain errors within MegaCommerce ecosystem."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# Security & Auth Exceptions
class AuthenticationError(MegaCommerceException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="UNAUTHENTICATED", status_code=401, details=details)


class AuthorizationError(MegaCommerceException):
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="FORBIDDEN", status_code=403, details=details)


class UserAlreadyExistsError(MegaCommerceException):
    def __init__(self, message: str = "User account already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="USER_EXISTS", status_code=409, details=details)


# Resource Exceptions
class ResourceNotFoundError(MegaCommerceException):
    def __init__(self, resource_name: str, resource_id: Any):
        super().__init__(
            message=f"{resource_name} with identifier '{resource_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource_name, "identifier": str(resource_id)}
        )


class InvalidStateTransitionError(MegaCommerceException):
    def __init__(self, entity: str, current_state: str, target_state: str):
        super().__init__(
            message=f"Cannot transition {entity} from '{current_state}' to '{target_state}'.",
            code="INVALID_STATE_TRANSITION",
            status_code=400,
            details={"entity": entity, "current_state": current_state, "target_state": target_state}
        )


# Commerce Domain Exceptions
class InsufficientStockError(MegaCommerceException):
    def __init__(self, sku: str, requested: int, available: int):
        super().__init__(
            message=f"Insufficient stock for SKU '{sku}'. Requested: {requested}, Available: {available}.",
            code="INSUFFICIENT_STOCK",
            status_code=400,
            details={"sku": sku, "requested": requested, "available": available}
        )


class PaymentSimulationError(MegaCommerceException):
    def __init__(self, message: str, transaction_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="PAYMENT_FAILED",
            status_code=402,
            details={"transaction_id": transaction_id} if transaction_id else {}
        )


class InvalidCouponError(MegaCommerceException):
    def __init__(self, coupon_code: str, reason: str):
        super().__init__(
            message=f"Coupon '{coupon_code}' is invalid: {reason}",
            code="INVALID_COUPON",
            status_code=400,
            details={"coupon_code": coupon_code, "reason": reason}
        )


class FraudRiskExceededError(MegaCommerceException):
    def __init__(self, order_id: str, risk_score: float, reason: str):
        super().__init__(
            message=f"Order '{order_id}' blocked due to high fraud risk score ({risk_score:.2f}): {reason}",
            code="FRAUD_RISK_EXCEEDED",
            status_code=403,
            details={"order_id": order_id, "risk_score": risk_score, "reason": reason}
        )


class ValidationCustomError(MegaCommerceException):
    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=errors or {})
