"""
MegaCommerce Analytics & Reporting Domain Service
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database.models.order import Order, OrderItem, PaymentTransaction
from database.models.user import User, SellerProfile, AuditLog
from database.models.catalog import Product, Category
from database.models.inventory import InventoryItem, Warehouse
from database.models.logistics import ReturnRequest
from database.models.analytics import FraudEvent, CustomerAnalyticsSummary, SellerAnalyticsSummary


class AnalyticsService:
    """Calculates real-time Customer, Seller, and Platform Admin Analytics."""

    def __init__(self, db: Session):
        self.db = db

    def get_customer_analytics(self, customer_id: str) -> Dict[str, Any]:
        """Calculates customer spending, order count, and purchase trends."""
        orders = self.db.query(Order).filter(Order.customer_id == customer_id).all()
        total_spent = sum([o.total_amount for o in orders if o.payment_status == "SUCCESS"])
        total_orders = len(orders)
        aov = round(total_spent / total_orders, 2) if total_orders > 0 else 0.0

        return {
            "customer_id": customer_id,
            "total_orders_placed": total_orders,
            "total_amount_spent": round(total_spent, 2),
            "average_order_value": aov,
            "customer_segment": "VIP" if total_spent > 1000.0 else "REGULAR"
        }

    def get_seller_analytics(self, seller_user_id: str) -> Dict[str, Any]:
        """Calculates seller revenue, order count, return rates, and top performing products."""
        seller = self.db.query(SellerProfile).filter(SellerProfile.user_id == seller_user_id).first()
        if not seller:
            return {"error": True, "message": "Seller profile not found."}

        order_items = (
            self.db.query(OrderItem)
            .filter(OrderItem.seller_id == seller.id)
            .all()
        )

        total_revenue = sum([item.total_price for item in order_items])
        total_orders = len(set([item.order_id for item in order_items]))

        products_count = self.db.query(func.count(Product.id)).filter(Product.seller_id == seller.id).scalar()

        return {
            "seller_id": seller.id,
            "company_name": seller.company_name,
            "store_name": seller.store_name,
            "total_products_listed": products_count,
            "total_orders_fulfilled": total_orders,
            "total_revenue_earned": round(total_revenue, 2),
            "rating_average": seller.rating_average,
            "seller_tier": "GOLD" if total_revenue > 5000.0 else "SILVER"
        }

    def get_platform_admin_analytics(self) -> Dict[str, Any]:
        """Calculates platform-wide revenue, order counts, active users, fraud events, and system audit logs."""
        total_users = self.db.query(func.count(User.id)).scalar()
        total_sellers = self.db.query(func.count(SellerProfile.id)).scalar()
        total_products = self.db.query(func.count(Product.id)).scalar()
        total_orders = self.db.query(func.count(Order.id)).scalar()
        total_revenue = self.db.query(func.sum(Order.total_amount)).filter(Order.payment_status == "SUCCESS").scalar() or 0.0

        flagged_fraud_count = self.db.query(func.count(FraudEvent.id)).filter(FraudEvent.flagged == True).scalar()
        recent_audits = (
            self.db.query(AuditLog)
            .order_by(desc(AuditLog.timestamp))
            .limit(10)
            .all()
        )

        return {
            "total_users": total_users,
            "total_sellers": total_sellers,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_gross_revenue": round(float(total_revenue), 2),
            "flagged_fraud_events": flagged_fraud_count,
            "recent_audit_logs": [
                {
                    "id": a.id,
                    "action": a.action,
                    "entity": a.entity_name,
                    "timestamp": a.timestamp.isoformat()
                } for a in recent_audits
            ]
        }
