"""MegaCommerce Shared Foundation Package"""
from shared.enums import (
    UserRole, UserStatus, ProductStatus, OrderStatus, PaymentStatus,
    PaymentMethod, ShipmentStatus, CouponType, ReturnReason, ReturnStatus,
    FraudRiskCategory, WarehouseZone, AuditAction
)
from shared.exceptions import (
    MegaCommerceException, AuthenticationError, AuthorizationError,
    UserAlreadyExistsError, ResourceNotFoundError, InvalidStateTransitionError,
    InsufficientStockError, PaymentSimulationError, InvalidCouponError,
    FraudRiskExceededError, ValidationCustomError
)
from shared.security import (
    hash_password, verify_password, create_access_token, decode_access_token, verify_user_role
)

__all__ = [
    "UserRole", "UserStatus", "ProductStatus", "OrderStatus", "PaymentStatus",
    "PaymentMethod", "ShipmentStatus", "CouponType", "ReturnReason", "ReturnStatus",
    "FraudRiskCategory", "WarehouseZone", "AuditAction",
    "MegaCommerceException", "AuthenticationError", "AuthorizationError",
    "UserAlreadyExistsError", "ResourceNotFoundError", "InvalidStateTransitionError",
    "InsufficientStockError", "PaymentSimulationError", "InvalidCouponError",
    "FraudRiskExceededError", "ValidationCustomError",
    "hash_password", "verify_password", "create_access_token", "decode_access_token", "verify_user_role"
]
