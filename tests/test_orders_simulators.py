"""
MegaCommerce Orders, Payment Simulator, and Delivery Simulator Test Suite
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from backend.services.auth_service import AuthService
from backend.services.catalog_service import CatalogService
from backend.services.cart_service import CartService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService
from backend.services.payment_simulator import PaymentSimulatorEngine
from backend.services.delivery_simulator import DeliverySimulatorEngine
from shared.enums import UserRole, PaymentMethod, OrderStatus, PaymentStatus, ShipmentStatus
from shared.dtos import (
    UserRegisterRequest, AddressCreateRequest, CategoryCreateRequest,
    ProductCreateRequest, CartItemAddRequest, CheckoutRequest, PaymentSimulateRequest
)
from shared.exceptions import PaymentSimulationError, InvalidStateTransitionError


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_full_order_checkout_payment_and_delivery_simulation_workflow(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    cart_svc = CartService(db_session)
    inv_svc = InventoryService(db_session)
    order_svc = OrderService(db_session)
    delivery_svc = DeliverySimulatorEngine(db_session)

    # 1. Register Customer & Seller
    cust = auth_svc.register_user(UserRegisterRequest(
        email="order_buyer@megacommerce.com", password="Password123!", first_name="Order", last_name="Buyer"
    ))
    seller = auth_svc.register_user(UserRegisterRequest(
        email="order_seller@megacommerce.com", password="Password123!", first_name="Order", last_name="Seller", role=UserRole.SELLER
    ))

    # Add Address
    addr = auth_svc.add_address(cust.user_id, AddressCreateRequest(
        title="Home", street_address="456 Tech Blvd", city="San Jose", state_province="CA", postal_code="95110", is_default=True
    ))

    # 2. Setup Warehouse & Stock
    wh = inv_svc.create_warehouse("Silicon Valley Hub", "WH-SJC-01", "100 Tech Way", "San Jose", "CA", "95110")
    cat = cat_svc.create_category(CategoryCreateRequest(name="Gadgets", slug="gadgets"))
    prod = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Smart Watch 5", slug="smart-watch-5", description="Fitness watch", category_id=cat.id, price=300.00, cost_price=180.00, stock_quantity=20
    ))
    inv_svc.add_stock(wh.id, prod.id, "WATCH-5", quantity=20)

    # 3. Add to Cart & Checkout
    cart_svc.add_to_cart(cust.user_id, CartItemAddRequest(product_id=prod.id, quantity=1))
    
    checkout_req = CheckoutRequest(
        shipping_address_id=addr.id,
        billing_address_id=addr.id,
        payment_method=PaymentMethod.CARD_SIMULATOR,
        order_notes="Please deliver before 5 PM"
    )
    order = order_svc.checkout_cart(cust.user_id, checkout_req)
    assert order.id is not None
    assert order.order_number.startswith("ORD-")
    assert order.payment_status == PaymentStatus.SUCCESS.value
    assert order.order_status == OrderStatus.CONFIRMED.value

    # 4. Logistics Delivery Simulation
    shipment = delivery_svc.create_shipment_for_order(order.id, wh.id)
    assert shipment.tracking_number is not None

    agent = delivery_svc.auto_assign_delivery_agent(shipment.id)
    assert agent.id is not None

    # Advance shipment to DELIVERED
    delivery_svc.update_shipment_status(shipment.id, ShipmentStatus.DELIVERED, "San Jose Customer Front Door", "Left package at front porch.")
    
    updated_order = order_svc.order_repo.get_by_id(order.id)
    assert updated_order.order_status == OrderStatus.DELIVERED.value


def test_payment_failure_simulation_handling(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    cart_svc = CartService(db_session)
    order_svc = OrderService(db_session)
    pay_engine = PaymentSimulatorEngine(db_session)

    cust = auth_svc.register_user(UserRegisterRequest(
        email="fail_buyer@megacommerce.com", password="Password123!", first_name="Fail", last_name="Buyer"
    ))
    seller = auth_svc.register_user(UserRegisterRequest(
        email="fail_seller@megacommerce.com", password="Password123!", first_name="Fail", last_name="Seller", role=UserRole.SELLER
    ))
    addr = auth_svc.add_address(cust.user_id, AddressCreateRequest(
        title="Home", street_address="789 Failure St", city="Dallas", state_province="TX", postal_code="75201"
    ))

    cat = cat_svc.create_category(CategoryCreateRequest(name="Games", slug="games"))
    prod = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Console X", slug="console-x", description="Gaming console", category_id=cat.id, price=500.00, cost_price=350.00, stock_quantity=5
    ))

    cart_svc.add_to_cart(cust.user_id, CartItemAddRequest(product_id=prod.id, quantity=1))
    order = order_svc.checkout_cart(cust.user_id, CheckoutRequest(
        shipping_address_id=addr.id, billing_address_id=addr.id, payment_method=PaymentMethod.CARD_SIMULATOR
    ))

    with pytest.raises(PaymentSimulationError):
        pay_engine.process_payment(PaymentSimulateRequest(
            order_id=order.id, payment_method=PaymentMethod.CARD_SIMULATOR, amount=500.00, simulate_failure=True
        ))
