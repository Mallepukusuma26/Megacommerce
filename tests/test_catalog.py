"""
MegaCommerce Catalog, Product, Category, and Variant Test Suite
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from backend.services.auth_service import AuthService
from backend.services.catalog_service import CatalogService
from shared.enums import UserRole
from shared.dtos import (
    UserRegisterRequest, CategoryCreateRequest, BrandCreateRequest,
    ProductCreateRequest, ProductVariantDTO
)


@pytest.fixture(scope="function")
def db_session():
    """Provides a clean in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_catalog_category_and_brand_creation(db_session):
    service = CatalogService(db_session)

    # 1. Create Category
    cat = service.create_category(CategoryCreateRequest(
        name="Electronics",
        slug="electronics",
        description="Gadgets and devices"
    ))
    assert cat.id is not None
    assert cat.slug == "electronics"

    # 2. Create Brand
    brand = service.create_brand(BrandCreateRequest(
        name="TechCorp",
        slug="techcorp",
        description="High tech devices"
    ))
    assert brand.id is not None
    assert brand.name == "TechCorp"


def test_product_creation_with_variants(db_session):
    auth_service = AuthService(db_session)
    catalog_service = CatalogService(db_session)

    # 1. Register Seller
    seller_resp = auth_service.register_user(UserRegisterRequest(
        email="seller_test@megacommerce.com",
        password="Password123!",
        first_name="Sam",
        last_name="Seller",
        company_name="Gadget Store",
        role=UserRole.SELLER
    ))

    # 2. Setup Category & Brand
    cat = catalog_service.create_category(CategoryCreateRequest(name="Smartphones", slug="smartphones"))
    brand = catalog_service.create_brand(BrandCreateRequest(name="Pear Inc", slug="pear-inc"))

    # 3. Create Product
    prod_req = ProductCreateRequest(
        title="PearPhone 15 Pro",
        slug="pearphone-15-pro",
        description="Latest flagship smartphone with titanium body.",
        category_id=cat.id,
        brand_id=brand.id,
        price=999.99,
        discount_price=949.99,
        cost_price=700.00,
        stock_quantity=50,
        variants=[
            ProductVariantDTO(sku="PP15P-128-BLK", variant_name="128GB Black", price=999.99, stock_quantity=30),
            ProductVariantDTO(sku="PP15P-256-SLV", variant_name="256GB Silver", price=1099.99, stock_quantity=20)
        ],
        images=["https://images.local/pearphone15.jpg"]
    )

    product = catalog_service.create_product(seller_resp.user_id, prod_req)
    assert product.id is not None
    assert product.title == "PearPhone 15 Pro"
    assert len(product.variants) == 2
    assert product.variants[0].sku == "PP15P-128-BLK"
    assert len(product.images) == 1


def test_filter_products_by_price_and_category(db_session):
    auth_service = AuthService(db_session)
    catalog_service = CatalogService(db_session)

    seller_resp = auth_service.register_user(UserRegisterRequest(
        email="filter_seller@megacommerce.com",
        password="Password123!",
        first_name="Filter",
        last_name="Seller",
        company_name="Filter Market",
        role=UserRole.SELLER
    ))

    cat_audio = catalog_service.create_category(CategoryCreateRequest(name="Audio", slug="audio"))
    cat_laptops = catalog_service.create_category(CategoryCreateRequest(name="Laptops", slug="laptops"))

    # Product 1: Headset $150
    catalog_service.create_product(seller_resp.user_id, ProductCreateRequest(
        title="Wireless Headset",
        slug="wireless-headset",
        description="ANC Headphones",
        category_id=cat_audio.id,
        price=150.00,
        cost_price=80.00,
        stock_quantity=100
    ))

    # Product 2: Pro Laptop $1200
    catalog_service.create_product(seller_resp.user_id, ProductCreateRequest(
        title="Pro Laptop 16",
        slug="pro-laptop-16",
        description="High performance laptop",
        category_id=cat_laptops.id,
        price=1200.00,
        cost_price=900.00,
        stock_quantity=25
    ))

    # Filter Audio Category
    audio_prods = catalog_service.filter_products(category_id=cat_audio.id)
    assert len(audio_prods) == 1
    assert audio_prods[0].title == "Wireless Headset"

    # Filter Max Price $500
    affordable_prods = catalog_service.filter_products(max_price=500.00)
    assert len(affordable_prods) == 1
    assert affordable_prods[0].title == "Wireless Headset"
