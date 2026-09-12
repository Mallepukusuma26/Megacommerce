"""
MegaCommerce Authentication & RBAC Test Suite
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from backend.services.auth_service import AuthService
from shared.enums import UserRole
from shared.dtos import UserRegisterRequest, UserLoginRequest, AddressCreateRequest
from shared.exceptions import UserAlreadyExistsError, AuthenticationError


@pytest.fixture(scope="function")
def db_session():
    """Provides a clean in-memory SQLite database session for each test function."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_user_registration_and_login_flow(db_session):
    service = AuthService(db_session)
    
    # 1. Register Customer
    reg_req = UserRegisterRequest(
        email="customer@megacommerce.com",
        password="SecurePassword123!",
        first_name="Alice",
        last_name="Customer",
        role=UserRole.CUSTOMER
    )
    auth_resp = service.register_user(reg_req)
    assert auth_resp.access_token is not None
    assert auth_resp.email == "customer@megacommerce.com"
    assert auth_resp.role == "CUSTOMER"

    # 2. Login Customer
    login_req = UserLoginRequest(
        email="customer@megacommerce.com",
        password="SecurePassword123!"
    )
    login_resp = service.authenticate_user(login_req)
    assert login_resp.access_token is not None
    assert login_resp.user_id == auth_resp.user_id

    # 3. Get Profile
    profile = service.get_user_profile(auth_resp.user_id)
    assert profile["first_name"] == "Alice"
    assert profile["email"] == "customer@megacommerce.com"


def test_seller_registration_creates_seller_profile(db_session):
    service = AuthService(db_session)
    reg_req = UserRegisterRequest(
        email="seller@megacommerce.com",
        password="SellerPassword123!",
        first_name="Bob",
        last_name="Seller",
        company_name="Acme Tech Trading",
        role=UserRole.SELLER
    )
    auth_resp = service.register_user(reg_req)
    assert auth_resp.role == "SELLER"

    profile = service.get_user_profile(auth_resp.user_id)
    assert "seller_profile" in profile
    assert profile["seller_profile"]["company_name"] == "Acme Tech Trading"


def test_duplicate_email_registration_raises_error(db_session):
    service = AuthService(db_session)
    reg_req = UserRegisterRequest(
        email="duplicate@megacommerce.com",
        password="Password123!",
        first_name="Dup",
        last_name="User",
        role=UserRole.CUSTOMER
    )
    service.register_user(reg_req)

    with pytest.raises(UserAlreadyExistsError):
        service.register_user(reg_req)


def test_invalid_login_credentials_raises_error(db_session):
    service = AuthService(db_session)
    reg_req = UserRegisterRequest(
        email="user@megacommerce.com",
        password="CorrectPassword123!",
        first_name="Test",
        last_name="User"
    )
    service.register_user(reg_req)

    with pytest.raises(AuthenticationError):
        service.authenticate_user(UserLoginRequest(email="user@megacommerce.com", password="WrongPassword!"))


def test_add_address_management(db_session):
    service = AuthService(db_session)
    auth_resp = service.register_user(UserRegisterRequest(
        email="address_test@megacommerce.com",
        password="Password123!",
        first_name="John",
        last_name="Doe"
    ))

    addr_req = AddressCreateRequest(
        title="Home",
        street_address="123 Commerce Way",
        city="Seattle",
        state_province="WA",
        postal_code="98101",
        is_default=True
    )
    addr = service.add_address(auth_resp.user_id, addr_req)
    assert addr.id is not None
    assert addr.city == "Seattle"

    profile = service.get_user_profile(auth_resp.user_id)
    assert len(profile["addresses"]) == 1
    assert profile["addresses"][0]["street_address"] == "123 Commerce Way"
