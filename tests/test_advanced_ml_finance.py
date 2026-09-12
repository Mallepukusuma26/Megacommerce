"""
MegaCommerce Advanced Services, PDF Invoices, Returns, Fraud, Demand & Sales ML Test Suite
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from backend.services.auth_service import AuthService
from backend.services.catalog_service import CatalogService
from backend.services.cart_service import CartService
from backend.services.order_service import OrderService
from backend.services.invoice_service import LocalInvoiceService
from backend.services.returns_refunds_service import ReturnsRefundsService
from ml_services.fraud_detector import LocalFraudDetector
from ml_services.demand_forecaster import LocalDemandForecaster
from ml_services.sales_predictor import LocalSalesPredictor
from shared.enums import UserRole, PaymentMethod, ReturnReason, OrderStatus, ReturnStatus
from shared.dtos import (
    UserRegisterRequest, AddressCreateRequest, CategoryCreateRequest,
    ProductCreateRequest, CartItemAddRequest, CheckoutRequest
)


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_pdf_invoice_generation(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    cart_svc = CartService(db_session)
    order_svc = OrderService(db_session)
    invoice_svc = LocalInvoiceService(db_session)

    cust = auth_svc.register_user(UserRegisterRequest(
        email="inv_buyer@megacommerce.com", password="Password123!", first_name="Invoice", last_name="Buyer"
    ))
    seller = auth_svc.register_user(UserRegisterRequest(
        email="inv_seller@megacommerce.com", password="Password123!", first_name="Invoice", last_name="Seller", role=UserRole.SELLER
    ))
    addr = auth_svc.add_address(cust.user_id, AddressCreateRequest(
        title="Home", street_address="100 Main St", city="Boston", state_province="MA", postal_code="02108"
    ))
    cat = cat_svc.create_category(CategoryCreateRequest(name="Office", slug="office"))
    prod = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Standing Desk", slug="standing-desk", description="Desk", category_id=cat.id, price=450.00, cost_price=300.00, stock_quantity=10
    ))

    cart_svc.add_to_cart(cust.user_id, CartItemAddRequest(product_id=prod.id, quantity=1))
    order = order_svc.checkout_cart(cust.user_id, CheckoutRequest(
        shipping_address_id=addr.id, billing_address_id=addr.id, payment_method=PaymentMethod.CARD_SIMULATOR
    ))

    pdf_file = invoice_svc.generate_pdf_invoice(order.id)
    assert pdf_file.exists()
    assert pdf_file.name.endswith(".pdf")


def test_returns_and_refund_workflow(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    cart_svc = CartService(db_session)
    order_svc = OrderService(db_session)
    returns_svc = ReturnsRefundsService(db_session)

    cust = auth_svc.register_user(UserRegisterRequest(
        email="ret_buyer@megacommerce.com", password="Password123!", first_name="Return", last_name="Buyer"
    ))
    seller = auth_svc.register_user(UserRegisterRequest(
        email="ret_seller@megacommerce.com", password="Password123!", first_name="Return", last_name="Seller", role=UserRole.SELLER
    ))
    addr = auth_svc.add_address(cust.user_id, AddressCreateRequest(
        title="Home", street_address="200 Return Way", city="Denver", state_province="CO", postal_code="80202"
    ))
    cat = cat_svc.create_category(CategoryCreateRequest(name="Apparel", slug="apparel"))
    prod = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Jacket", slug="jacket", description="Warm jacket", category_id=cat.id, price=100.00, cost_price=60.00, stock_quantity=10
    ))

    cart_svc.add_to_cart(cust.user_id, CartItemAddRequest(product_id=prod.id, quantity=1))
    order = order_svc.checkout_cart(cust.user_id, CheckoutRequest(
        shipping_address_id=addr.id, billing_address_id=addr.id, payment_method=PaymentMethod.CARD_SIMULATOR
    ))

    # 1. Customer Submits Return
    ret_req = returns_svc.create_return_request(cust.user_id, order.id, ReturnReason.WRONG_ITEM, "Item received was red instead of blue.")
    assert ret_req.status == ReturnStatus.REQUESTED.value

    # 2. Inspection & Refund Execution
    ret_req = returns_svc.process_return_inspection(ret_req.id, passed_inspection=True, notes="Verified wrong color item received.")
    assert ret_req.status == ReturnStatus.REFUNDED.value
    assert ret_req.refund_transaction is not None


def test_fraud_detector_anomaly_scoring(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    cart_svc = CartService(db_session)
    order_svc = OrderService(db_session)
    fraud_detector = LocalFraudDetector(db_session)

    cust = auth_svc.register_user(UserRegisterRequest(
        email="fraud_buyer@megacommerce.com", password="Password123!", first_name="Fraud", last_name="Test"
    ))
    seller = auth_svc.register_user(UserRegisterRequest(
        email="fraud_seller@megacommerce.com", password="Password123!", first_name="Fraud", last_name="Seller", role=UserRole.SELLER
    ))
    addr = auth_svc.add_address(cust.user_id, AddressCreateRequest(
        title="Home", street_address="300 High Risk St", city="Miami", state_province="FL", postal_code="33101"
    ))

    cat = cat_svc.create_category(CategoryCreateRequest(name="Jewelry", slug="jewelry"))
    prod = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Gold Diamond Ring", slug="gold-diamond-ring", description="Expensive Ring", category_id=cat.id, price=3000.00, cost_price=2000.00, stock_quantity=5
    ))

    cart_svc.add_to_cart(cust.user_id, CartItemAddRequest(product_id=prod.id, quantity=1))
    order = order_svc.checkout_cart(cust.user_id, CheckoutRequest(
        shipping_address_id=addr.id, billing_address_id=addr.id, payment_method=PaymentMethod.CARD_SIMULATOR
    ))

    assessment = fraud_detector.evaluate_order_risk(order.id)
    assert assessment.risk_score >= 0.35
    assert len(assessment.risk_reasons) >= 1


def test_demand_forecasting_and_sales_prediction(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    forecaster = LocalDemandForecaster(db_session)
    predictor = LocalSalesPredictor(db_session)

    seller = auth_svc.register_user(UserRegisterRequest(
        email="ml_seller@megacommerce.com", password="Password123!", first_name="ML", last_name="Seller", role=UserRole.SELLER
    ))
    cat = cat_svc.create_category(CategoryCreateRequest(name="Software", slug="software"))
    prod = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Security Suite Pro", slug="security-suite-pro", description="AV", category_id=cat.id, price=50.00, cost_price=10.00, stock_quantity=100
    ))

    # Demand Forecast
    forecast = forecaster.forecast_product_demand(prod.id, horizon_days=30)
    assert forecast["total_predicted_demand_units"] >= 0
    assert len(forecast["daily_forecasts"]) == 30

    # Sales Prediction
    sales_pred = predictor.predict_platform_monthly_revenue(months_ahead=6)
    assert len(sales_pred["predictions"]) == 6
    assert sales_pred["predictions"][0]["predicted_revenue"] > 0
