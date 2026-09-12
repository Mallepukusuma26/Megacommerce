"""
MegaCommerce Cart & Wishlist Domain Service
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from database.models.cart_wishlist import Cart, CartItem, Wishlist, WishlistItem
from database.models.catalog import Product, ProductVariant
from database.models.promotions import Coupon
from database.repositories.domain_repositories import BaseRepository
from shared.exceptions import ResourceNotFoundError, InsufficientStockError, InvalidCouponError
from shared.dtos import CartItemAddRequest, CartResponse, CartItemResponse
from config.settings import settings


class CartService:
    """Core domain service for Cart calculation, persistence, discount validation, and Wishlists."""

    def __init__(self, db: Session):
        self.db = db
        self.cart_repo = BaseRepository(Cart, db)
        self.cart_item_repo = BaseRepository(CartItem, db)
        self.wishlist_repo = BaseRepository(Wishlist, db)

    def get_or_create_cart(self, user_id: str) -> Cart:
        """Retrieves existing active shopping cart or creates new one for user."""
        cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            self.db.commit()
        return cart

    def add_to_cart(self, user_id: str, req: CartItemAddRequest) -> CartItem:
        """Adds a product or variant item to the customer's cart."""
        cart = self.get_or_create_cart(user_id)
        
        # Validate Product & Stock
        product = self.db.query(Product).filter(Product.id == req.product_id).first()
        if not product:
            raise ResourceNotFoundError("Product", req.product_id)

        unit_price = product.discount_price or product.price
        available_stock = product.stock_quantity

        if req.variant_sku:
            variant = self.db.query(ProductVariant).filter(ProductVariant.sku == req.variant_sku).first()
            if variant:
                unit_price = variant.discount_price or variant.price
                available_stock = variant.stock_quantity

        if available_stock < req.quantity:
            raise InsufficientStockError(
                sku=req.variant_sku or product.slug,
                requested=req.quantity,
                available=available_stock
            )

        # Check existing cart item
        item = self.db.query(CartItem).filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == req.product_id,
            CartItem.variant_sku == req.variant_sku
        ).first()

        if item:
            item.quantity += req.quantity
            item.unit_price = unit_price
        else:
            item = CartItem(
                cart_id=cart.id,
                product_id=req.product_id,
                variant_sku=req.variant_sku,
                quantity=req.quantity,
                unit_price=unit_price
            )
            self.db.add(item)

        self.db.commit()
        return item

    def update_cart_item_quantity(self, user_id: str, item_id: str, quantity: int) -> CartItem:
        """Updates quantity of an existing cart item."""
        cart = self.get_or_create_cart(user_id)
        item = self.cart_item_repo.get_by_id_or_raise(item_id)
        if item.cart_id != cart.id:
            raise ResourceNotFoundError("CartItem", item_id)

        if quantity <= 0:
            self.db.delete(item)
            self.db.commit()
            return None

        item.quantity = quantity
        self.db.commit()
        return item

    def remove_from_cart(self, user_id: str, item_id: str) -> bool:
        """Removes an item from customer's cart."""
        cart = self.get_or_create_cart(user_id)
        item = self.cart_item_repo.get_by_id_or_raise(item_id)
        if item.cart_id == cart.id:
            self.db.delete(item)
            self.db.commit()
            return True
        return False

    def apply_coupon(self, user_id: str, coupon_code: str) -> Cart:
        """Validates and applies a coupon code to customer's cart."""
        cart = self.get_or_create_cart(user_id)
        coupon = self.db.query(Coupon).filter(Coupon.code == coupon_code.upper().strip()).first()
        if not coupon or not coupon.is_active:
            raise InvalidCouponError(coupon_code, "Coupon code is invalid or inactive.")

        cart.applied_coupon_code = coupon.code
        self.db.commit()
        return cart

    def calculate_cart_summary(self, user_id: str) -> CartResponse:
        """Calculates itemized subtotal, discount, tax, shipping, and grand total for checkout."""
        cart = self.get_or_create_cart(user_id)
        
        items_dto: List[CartItemResponse] = []
        subtotal = 0.0

        for i in cart.items:
            item_total = i.unit_price * i.quantity
            subtotal += item_total
            items_dto.append(CartItemResponse(
                id=i.id,
                product_id=i.product_id,
                product_title=i.product.title,
                variant_sku=i.variant_sku,
                price=i.unit_price,
                quantity=i.quantity,
                subtotal=item_total,
                image_url=i.product.images[0].image_url if i.product.images else None
            ))

        # Discount calculation
        discount_total = 0.0
        if cart.applied_coupon_code:
            coupon = self.db.query(Coupon).filter(Coupon.code == cart.applied_coupon_code).first()
            if coupon and subtotal >= coupon.min_order_value:
                if coupon.coupon_type == "PERCENTAGE":
                    discount_total = subtotal * (coupon.discount_value / 100.0)
                else:
                    discount_total = coupon.discount_value
                if coupon.max_discount_amount:
                    discount_total = min(discount_total, coupon.max_discount_amount)

        tax_total = (subtotal - discount_total) * settings.simulators.TAX_RATE
        shipping_total = 0.0 if (subtotal >= settings.simulators.FREE_SHIPPING_THRESHOLD or subtotal == 0) else settings.simulators.DEFAULT_SHIPPING_FEE
        grand_total = max(0.0, (subtotal - discount_total) + tax_total + shipping_total)

        return CartResponse(
            items=items_dto,
            subtotal=round(subtotal, 2),
            discount_total=round(discount_total, 2),
            tax_total=round(tax_total, 2),
            shipping_total=round(shipping_total, 2),
            grand_total=round(grand_total, 2),
            applied_coupon_code=cart.applied_coupon_code
        )
