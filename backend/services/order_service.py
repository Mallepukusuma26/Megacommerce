"""
MegaCommerce Order Lifecycle & State Machine Service
"""

import datetime
import random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.order import Order, OrderItem, OrderHistory
from database.models.cart_wishlist import Cart, CartItem
from database.models.catalog import Product
from database.models.user import Address, AuditLog
from database.repositories.domain_repositories import OrderRepository, BaseRepository
from backend.services.cart_service import CartService
from backend.services.inventory_service import InventoryService
from backend.services.payment_simulator import PaymentSimulatorEngine
from backend.services.delivery_simulator import DeliverySimulatorEngine
from shared.enums import OrderStatus, PaymentStatus, PaymentMethod, AuditAction
from shared.exceptions import (
    ResourceNotFoundError, InvalidStateTransitionError, InsufficientStockError
)
from shared.dtos import CheckoutRequest, PaymentSimulateRequest, OrderResponse


def generate_order_number() -> str:
    return f"ORD-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


ALLOWED_STATE_TRANSITIONS = {
    OrderStatus.CREATED.value: [OrderStatus.PAYMENT_PENDING.value, OrderStatus.CANCELLED.value],
    OrderStatus.PAYMENT_PENDING.value: [OrderStatus.PAYMENT_SUCCESS.value, OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value],
    OrderStatus.PAYMENT_SUCCESS.value: [OrderStatus.CONFIRMED.value, OrderStatus.PROCESSING.value, OrderStatus.CANCELLED.value],
    OrderStatus.CONFIRMED.value: [OrderStatus.PROCESSING.value, OrderStatus.CANCELLED.value],
    OrderStatus.PROCESSING.value: [OrderStatus.PACKED.value, OrderStatus.CANCELLED.value],
    OrderStatus.PACKED.value: [OrderStatus.SHIPPED.value, OrderStatus.CANCELLED.value],
    OrderStatus.SHIPPED.value: [OrderStatus.OUT_FOR_DELIVERY.value, OrderStatus.DELIVERED.value],
    OrderStatus.OUT_FOR_DELIVERY.value: [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value],
    OrderStatus.DELIVERED.value: [OrderStatus.RETURN_REQUESTED.value],
    OrderStatus.CANCELLED.value: [],
}


class OrderService:
    """Core domain service for complete Order Lifecycle management."""

    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_service = CartService(db)
        self.inventory_service = InventoryService(db)
        self.payment_engine = PaymentSimulatorEngine(db)
        self.delivery_engine = DeliverySimulatorEngine(db)

    def checkout_cart(self, customer_id: str, req: CheckoutRequest) -> Order:
        """Executes full order placement workflow from customer cart."""
        cart_summary = self.cart_service.calculate_cart_summary(customer_id)
        if not cart_summary.items:
            raise InvalidStateTransitionError("Cart", "EMPTY", "ORDER_CREATED")

        # Validate Addresses
        shipping_addr = self.db.query(Address).filter(Address.id == req.shipping_address_id).first()
        if not shipping_addr:
            raise ResourceNotFoundError("Address", req.shipping_address_id)

        order_num = generate_order_number()

        # 1. Instantiate Order
        order = Order(
            order_number=order_num,
            customer_id=customer_id,
            shipping_address_id=req.shipping_address_id,
            billing_address_id=req.billing_address_id,
            order_status=OrderStatus.CREATED.value,
            payment_status=PaymentStatus.PENDING.value,
            payment_method=req.payment_method.value if isinstance(req.payment_method, PaymentMethod) else str(req.payment_method),
            subtotal=cart_summary.subtotal,
            discount_amount=cart_summary.discount_total,
            tax_amount=cart_summary.tax_total,
            shipping_amount=cart_summary.shipping_total,
            total_amount=cart_summary.grand_total,
            coupon_code=req.coupon_code or cart_summary.applied_coupon_code,
            notes=req.order_notes
        )
        self.db.add(order)
        self.db.flush()

        # 2. Create OrderItems & Reserve Stock
        for item in cart_summary.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise ResourceNotFoundError("Product", item.product_id)

            order_item = OrderItem(
                order_id=order.id,
                seller_id=product.seller_id,
                product_id=product.id,
                product_title=product.title,
                sku=item.variant_sku or product.slug,
                unit_price=item.price,
                quantity=item.quantity,
                total_price=item.subtotal
            )
            self.db.add(order_item)

            # Reserve Stock
            try:
                self.inventory_service.reserve_stock(
                    order_id=order.id,
                    sku=item.variant_sku or product.slug,
                    quantity=item.quantity
                )
            except InsufficientStockError:
                # Fallback update for simple products
                product.stock_quantity = max(0, product.stock_quantity - item.quantity)

        # Record State History
        hist = OrderHistory(
            order_id=order.id,
            from_status=None,
            to_status=OrderStatus.CREATED.value,
            notes="Order placed by customer."
        )
        self.db.add(hist)
        self.db.commit()

        # 3. Simulate Payment
        pay_req = PaymentSimulateRequest(
            order_id=order.id,
            payment_method=req.payment_method,
            amount=order.total_amount
        )
        try:
            self.payment_engine.process_payment(pay_req)
        except Exception as e:
            order.payment_status = PaymentStatus.FAILED.value
            self.db.commit()

        # 4. Clear Customer Cart
        cart = self.cart_service.get_or_create_cart(customer_id)
        self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        cart.applied_coupon_code = None
        self.db.commit()

        return order

    def update_order_status(self, order_id: str, target_status: OrderStatus, changed_by_user_id: Optional[str] = None, notes: Optional[str] = None) -> Order:
        """Enforces valid state machine transition for order lifecycle."""
        order = self.order_repo.get_by_id_or_raise(order_id)
        target_val = target_status.value if isinstance(target_status, OrderStatus) else str(target_status)

        current_val = order.order_status
        allowed = ALLOWED_STATE_TRANSITIONS.get(current_val, [])
        if target_val not in allowed and target_val != current_val:
            raise InvalidStateTransitionError("Order", current_val, target_val)

        order.order_status = target_val
        hist = OrderHistory(
            order_id=order.id,
            from_status=current_val,
            to_status=target_val,
            changed_by_user_id=changed_by_user_id,
            notes=notes or f"Status updated to {target_val}"
        )
        self.db.add(hist)
        self.db.commit()
        return order
