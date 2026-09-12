"""
MegaCommerce Specialized Domain Repositories
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, desc
from database.models import (
    User, Address, SellerProfile, Product, Category, Brand,
    Order, OrderItem, InventoryItem, Warehouse, Cart, CartItem,
    PaymentTransaction, Review, Coupon, Shipment, AuditLog
)
from database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        return self.session.execute(stmt).scalar_one_or_none()


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: Session):
        super().__init__(Product, session)

    def get_by_slug(self, slug: str) -> Optional[Product]:
        stmt = select(Product).where(Product.slug == slug)
        return self.session.execute(stmt).scalar_one_or_none()

    def filter_products(
        self,
        category_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        seller_id: Optional[str] = None,
        status: Optional[str] = "APPROVED",
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        conditions = []
        if status:
            conditions.append(Product.status == status)
        if category_id:
            conditions.append(Product.category_id == category_id)
        if brand_id:
            conditions.append(Product.brand_id == brand_id)
        if seller_id:
            conditions.append(Product.seller_id == seller_id)
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        if min_rating is not None:
            conditions.append(Product.rating_average >= min_rating)

        stmt = select(Product).where(and_(*conditions)).offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: Session):
        super().__init__(Order, session)

    def get_by_order_number(self, order_number: str) -> Optional[Order]:
        stmt = select(Order).where(Order.order_number == order_number)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_customer_orders(self, customer_id: str, skip: int = 0, limit: int = 20) -> List[Order]:
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_seller_orders(self, seller_id: str, skip: int = 0, limit: int = 20) -> List[Order]:
        stmt = (
            select(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(OrderItem.seller_id == seller_id)
            .distinct()
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())


class InventoryRepository(BaseRepository[InventoryItem]):
    def __init__(self, session: Session):
        super().__init__(InventoryItem, session)

    def get_by_sku(self, sku: str, warehouse_id: Optional[str] = None) -> Optional[InventoryItem]:
        conditions = [InventoryItem.sku == sku]
        if warehouse_id:
            conditions.append(InventoryItem.warehouse_id == warehouse_id)
        stmt = select(InventoryItem).where(and_(*conditions))
        return self.session.execute(stmt).scalars().first()

    def get_low_stock_items(self, threshold_override: Optional[int] = None) -> List[InventoryItem]:
        stmt = select(InventoryItem).where(
            InventoryItem.quantity_available <= InventoryItem.reorder_threshold
        )
        return list(self.session.execute(stmt).scalars().all())
