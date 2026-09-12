"""
MegaCommerce Local Search Engine & Local Recommendation Engine Test Suite
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base
from backend.services.auth_service import AuthService
from backend.services.catalog_service import CatalogService
from ml_services.search_engine import LocalSearchEngine
from ml_services.recommendation_engine import LocalRecommendationEngine
from shared.enums import UserRole
from shared.dtos import UserRegisterRequest, CategoryCreateRequest, BrandCreateRequest, ProductCreateRequest, SearchRequest


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_local_vector_tfidf_search_engine(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    search_engine = LocalSearchEngine(db_session)

    seller = auth_svc.register_user(UserRegisterRequest(
        email="search_seller@megacommerce.com", password="Password123!", first_name="Search", last_name="Seller", role=UserRole.SELLER
    ))
    cat_laptop = cat_svc.create_category(CategoryCreateRequest(name="Laptops", slug="laptops"))
    cat_audio = cat_svc.create_category(CategoryCreateRequest(name="Audio", slug="audio"))
    brand = cat_svc.create_brand(BrandCreateRequest(name="AudioTech", slug="audiotech"))

    # Add Products
    p1 = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="AudioTech Wireless Headphones", slug="audiotech-wireless-headphones", description="Noise cancelling bluetooth headphones", category_id=cat_audio.id, brand_id=brand.id, price=199.99, cost_price=100.00, stock_quantity=50
    ))

    p2 = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Gaming Laptop Ultra", slug="gaming-laptop-ultra", description="High performance gaming laptop with 32GB RAM", category_id=cat_laptop.id, price=1500.00, cost_price=1000.00, stock_quantity=15
    ))

    # 1. Search Query "Headphones"
    results = search_engine.search(SearchRequest(query="Headphones"))
    assert len(results) >= 1
    assert results[0]["product_id"] == p1.id
    assert results[0]["relevance_score"] > 0

    # 2. Facet Search Category Audio
    audio_results = search_engine.search(SearchRequest(query="Audio", category_id=cat_audio.id))
    assert len(audio_results) == 1
    assert audio_results[0]["product_id"] == p1.id

    # 3. Suggestions
    suggestions = search_engine.get_search_suggestions("Gaming")
    assert len(suggestions) >= 1
    assert "Gaming Laptop Ultra" in suggestions[0]


def test_local_recommendation_engine_similar_and_popular(db_session):
    auth_svc = AuthService(db_session)
    cat_svc = CatalogService(db_session)
    rec_engine = LocalRecommendationEngine(db_session)

    seller = auth_svc.register_user(UserRegisterRequest(
        email="rec_seller@megacommerce.com", password="Password123!", first_name="Rec", last_name="Seller", role=UserRole.SELLER
    ))
    cat = cat_svc.create_category(CategoryCreateRequest(name="Cameras", slug="cameras"))

    p1 = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="4K DSLR Camera", slug="4k-dslr-camera", description="Professional 4K DSLR camera with 24MP sensor", category_id=cat.id, price=899.99, cost_price=600.00, stock_quantity=10
    ))
    p2 = cat_svc.create_product(seller.user_id, ProductCreateRequest(
        title="Camera Zoom Lens 50mm", slug="camera-zoom-lens-50mm", description="DSLR camera 50mm prime lens", category_id=cat.id, price=299.99, cost_price=180.00, stock_quantity=15
    ))

    # Similar Products to p1 (DSLR Camera)
    sim_recs = rec_engine.get_similar_products(p1.id)
    assert len(sim_recs) == 1
    assert sim_recs[0]["product_id"] == p2.id

    # Popular Products
    pop_recs = rec_engine.get_popular_products()
    assert len(pop_recs) == 2
