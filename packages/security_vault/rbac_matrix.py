"""
MegaCommerce Security Vault — Granular RBAC Permission Matrix
"""

from typing import Set, Dict, List
from shared.enums import UserRole


class SystemPermissions:
    # Catalog
    CATALOG_VIEW = "catalog:view"
    CATALOG_CREATE = "catalog:create"
    CATALOG_EDIT = "catalog:edit"
    CATALOG_DELETE = "catalog:delete"
    CATALOG_APPROVE = "catalog:approve"

    # Orders & Cart
    CART_MANAGE = "cart:manage"
    ORDER_CREATE = "order:create"
    ORDER_VIEW_OWN = "order:view_own"
    ORDER_VIEW_ALL = "order:view_all"
    ORDER_STATUS_UPDATE = "order:status_update"
    ORDER_CANCEL = "order:cancel"

    # Inventory & Warehouse
    STOCK_VIEW = "stock:view"
    STOCK_ADJUST = "stock:adjust"
    WAREHOUSE_MANAGE = "warehouse:manage"
    LOGISTICS_DISPATCH = "logistics:dispatch"

    # Finance & Refunds
    PAYMENT_SIMULATE = "payment:simulate"
    REFUND_PROCESS = "refund:process"
    INVOICE_GENERATE = "invoice:generate"

    # Admin & Security
    USER_MANAGE = "user:manage"
    AUDIT_VIEW = "audit:view"
    FRAUD_MONITOR = "fraud:monitor"
    ANALYTICS_VIEW = "analytics:view"


ROLE_PERMISSIONS_MATRIX: Dict[str, Set[str]] = {
    UserRole.CUSTOMER.value: {
        SystemPermissions.CATALOG_VIEW,
        SystemPermissions.CART_MANAGE,
        SystemPermissions.ORDER_CREATE,
        SystemPermissions.ORDER_VIEW_OWN,
        SystemPermissions.ORDER_CANCEL,
        SystemPermissions.PAYMENT_SIMULATE,
        SystemPermissions.INVOICE_GENERATE
    },
    UserRole.SELLER.value: {
        SystemPermissions.CATALOG_VIEW,
        SystemPermissions.CATALOG_CREATE,
        SystemPermissions.CATALOG_EDIT,
        SystemPermissions.STOCK_VIEW,
        SystemPermissions.STOCK_ADJUST,
        SystemPermissions.ORDER_VIEW_OWN,
        SystemPermissions.ORDER_STATUS_UPDATE,
        SystemPermissions.ANALYTICS_VIEW
    },
    UserRole.ADMIN.value: {
        SystemPermissions.CATALOG_VIEW,
        SystemPermissions.CATALOG_CREATE,
        SystemPermissions.CATALOG_EDIT,
        SystemPermissions.CATALOG_DELETE,
        SystemPermissions.CATALOG_APPROVE,
        SystemPermissions.CART_MANAGE,
        SystemPermissions.ORDER_CREATE,
        SystemPermissions.ORDER_VIEW_OWN,
        SystemPermissions.ORDER_VIEW_ALL,
        SystemPermissions.ORDER_STATUS_UPDATE,
        SystemPermissions.ORDER_CANCEL,
        SystemPermissions.STOCK_VIEW,
        SystemPermissions.STOCK_ADJUST,
        SystemPermissions.WAREHOUSE_MANAGE,
        SystemPermissions.LOGISTICS_DISPATCH,
        SystemPermissions.PAYMENT_SIMULATE,
        SystemPermissions.REFUND_PROCESS,
        SystemPermissions.INVOICE_GENERATE,
        SystemPermissions.USER_MANAGE,
        SystemPermissions.AUDIT_VIEW,
        SystemPermissions.FRAUD_MONITOR,
        SystemPermissions.ANALYTICS_VIEW
    },
    UserRole.WAREHOUSE_MANAGER.value: {
        SystemPermissions.CATALOG_VIEW,
        SystemPermissions.STOCK_VIEW,
        SystemPermissions.STOCK_ADJUST,
        SystemPermissions.WAREHOUSE_MANAGE,
        SystemPermissions.LOGISTICS_DISPATCH,
        SystemPermissions.ORDER_STATUS_UPDATE
    },
    UserRole.DELIVERY_AGENT.value: {
        SystemPermissions.LOGISTICS_DISPATCH,
        SystemPermissions.ORDER_STATUS_UPDATE
    },
    UserRole.SYSTEM_AUDITOR.value: {
        SystemPermissions.AUDIT_VIEW,
        SystemPermissions.FRAUD_MONITOR,
        SystemPermissions.ANALYTICS_VIEW
    }
}


class RBACAuthorityChecker:
    """Checks role permissions against granular system permissions."""

    @staticmethod
    def has_permission(user_role: str, permission: str) -> bool:
        user_perms = ROLE_PERMISSIONS_MATRIX.get(user_role, set())
        return permission in user_perms
