"""
MegaCommerce Inventory & Cart/Wishlist Test Suite
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from database.models.promotions import Coupon
from backend.services.auth_service import AuthService
from backend.services.catalog_service import CatalogService
from backend.services.inventory_service import InventoryService
from backend.services.cart_service import CartService
from shared.enums import UserRole
from shared.dtos import UserRegisterRequest, CategoryCreateRequest, ProductCreateRequest, CartItemAddRequest
from shared.exceptions import InsufficientStockError, InvalidCouponError


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_inventory_warehouse_stock_allocation_and_reservations(db_session):
    inv_service = InventoryService(db_session)
    auth_service = AuthService(db_session)
    cat_service = CatalogService(db_session)

    # 1. Register Seller & Create Product
    seller = auth_service.register_user(UserRegisterRequest(
        email="wh_seller@megacommerce.com", password="Password123!", first_name="Warehouse", last_name="Seller", role=UserRole.SELLER
    ))
    cat = cat_service.create_category(CategoryCreateRequest(name="Tools", slug="tools"))
    product = cat_service.create_product(seller.user_id, ProductCreateRequest(
        title="Drill Set", slug="drill-set", description="Power drill", category_id=cat.id, price=120.00, cost_price=70.00, stock_quantity=0
    ))

    # 2. Register Warehouse & Add Stock
    wh = inv_service.create_warehouse("Seattle Main Hub", "WH-SEA-01", "100 Industrial Way", "Seattle", "WA", "98101")
    item = inv_service.add_stock(wh.id, product.id, "DRILL-01", quantity=50)
    assert item.quantity_available == 50

    # 3. Reserve Stock for Order
    res = inv_service.reserve_stock(order_id="ORD-1001", sku="DRILL-01", quantity=5)
    assert res.id is not None
    assert item.quantity_available == 45
    assert item.quantity_reserved == 5

    # 4. Fulfill Reservation
    inv_service.release_or_fulfill_reservation(res.id, fulfill=True)
    assert item.quantity_reserved == 0


def test_cart_item_addition_calculation_and_coupon(db_session):
    auth_service = AuthService(db_session)
    cat_service = CatalogService(db_session)
    cart_service = CartService(db_session)

    customer = auth_service.register_user(UserRegisterRequest(
        email="buyer@megacommerce.com", password="Password123!", first_name="Jane", last_name="Buyer"
    ))
    seller = auth_service.register_user(UserRegisterRequest(
        email="cart_seller@megacommerce.com", password="Password123!", first_name="Cart", last_name="Seller", role=UserRole.SELLER
    ))

    cat = cat_service.create_category(CategoryCreateRequest(name="Home", slug="home"))
    product = cat_service.create_product(seller.user_id, ProductCreateRequest(
        title="Ergonomic Chair", slug="ergo-chair", description="Office chair", category_id=cat.id, price=200.00, cost_price=120.00, stock_quantity=10
    ))

    # Add 2 Chairs to Cart ($400 Subtotal)
    cart_service.add_to_cart(customer.user_id, CartItemAddRequest(product_id=product.id, quantity=2))

    summary = cart_service.calculate_cart_summary(customer.user_id)
    assert len(summary.items) == 1
    assert summary.subtotal == 400.00
    assert summary.shipping_total == 0.0  # Free shipping over $100

    # Create & Apply Coupon "SAVE10" (10% off)
    coupon = Coupon(
        code="SAVE10",
        coupon_type="PERCENTAGE",
        discount_value=10.0,
        start_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(days=7),
        is_active=True
    )
    db_session.add(coupon)
    db_session.commit()

    cart_service.apply_coupon(customer.user_id, "SAVE10")
    summary_with_coupon = cart_service.calculate_cart_summary(customer.user_id)
    assert summary_with_coupon.discount_total == 40.00
    assert summary_with_coupon.grand_total == round((400.0 - 40.0) * 1.08, 2)


def test_cart_insufficient_stock_raises_error(db_session):
    auth_service = AuthService(db_session)
    cat_service = CatalogService(db_session)
    cart_service = CartService(db_session)

    customer = auth_service.register_user(UserRegisterRequest(
        email="stock_buyer@megacommerce.com", password="Password123!", first_name="Stock", last_name="Buyer"
    ))
    seller = auth_service.register_user(UserRegisterRequest(
        email="low_stock_seller@megacommerce.com", password="Password123!", first_name="Low", last_name="Seller", role=UserRole.SELLER
    ))

    cat = cat_service.create_category(CategoryCreateRequest(name="Books", slug="books"))
    product = cat_service.create_product(seller.user_id, ProductCreateRequest(
        title="Limited Novel", slug="limited-novel", description="Book", category_id=cat.id, price=25.00, cost_price=10.00, stock_quantity=2
    ))

    with pytest.raises(InsufficientStockError):
        cart_service.add_to_cart(customer.user_id, CartItemAddRequest(product_id=product.id, quantity=5))
