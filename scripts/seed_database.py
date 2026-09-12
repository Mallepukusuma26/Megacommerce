"""
MegaCommerce Database Seeding Script
Populates initial sample categories, brands, products, warehouses, sellers, and customers.
"""

from database.connection import init_db, SessionLocal
from backend.services.auth_service import AuthService
from backend.services.catalog_service import CatalogService
from backend.services.inventory_service import InventoryService
from shared.enums import UserRole
from shared.dtos import UserRegisterRequest, CategoryCreateRequest, BrandCreateRequest, ProductCreateRequest, ProductVariantDTO


def seed_database():
    init_db()
    db = SessionLocal()
    try:
        auth_svc = AuthService(db)
        cat_svc = CatalogService(db)
        inv_svc = InventoryService(db)

        print("Seeding Users...")
        # 1. Admin User
        admin_resp = auth_svc.register_user(UserRegisterRequest(
            email="admin@megacommerce.com", password="AdminPassword123!", first_name="System", last_name="Admin", role=UserRole.ADMIN
        ))

        # 2. Seller User
        seller_resp = auth_svc.register_user(UserRegisterRequest(
            email="seller@megacommerce.com", password="SellerPassword123!", first_name="Nexus", last_name="Seller", company_name="Nexus Electronics", role=UserRole.SELLER
        ))

        # 3. Customer User
        customer_resp = auth_svc.register_user(UserRegisterRequest(
            email="customer@megacommerce.com", password="CustomerPassword123!", first_name="John", last_name="Customer", role=UserRole.CUSTOMER
        ))

        print("Seeding Categories & Brands...")
        c_elec = cat_svc.create_category(CategoryCreateRequest(name="Electronics & Gadgets", slug="electronics"))
        c_home = cat_svc.create_category(CategoryCreateRequest(name="Home & Office", slug="home-office"))
        
        b_apex = cat_svc.create_brand(BrandCreateRequest(name="ApexTech", slug="apextech"))
        b_luxe = cat_svc.create_brand(BrandCreateRequest(name="LuxeLiving", slug="luxeliving"))

        print("Seeding Warehouses & Stock...")
        wh1 = inv_svc.create_warehouse("West Coast Fulfillment Hub", "WH-WST-01", "500 Logistics Way", "Seattle", "WA", "98101")
        wh2 = inv_svc.create_warehouse("East Coast Fulfillment Hub", "WH-EST-01", "800 Harbor Rd", "Boston", "MA", "02108")

        print("Seeding Products...")
        p1 = cat_svc.create_product(seller_resp.user_id, ProductCreateRequest(
            title="ApexPad Pro 12.9 Inch",
            slug="apexpad-pro-129",
            description="Ultra high definition tablet computer with M2 chip and Retina display.",
            category_id=c_elec.id,
            brand_id=b_apex.id,
            price=1099.99,
            discount_price=999.99,
            cost_price=750.00,
            stock_quantity=45,
            variants=[
                ProductVariantDTO(sku="APEX-129-128", variant_name="128GB Wi-Fi", price=999.99, stock_quantity=25),
                ProductVariantDTO(sku="APEX-129-256", variant_name="256GB Cellular", price=1199.99, stock_quantity=20)
            ],
            images=["https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600"]
        ))
        inv_svc.add_stock(wh1.id, p1.id, "APEX-129-128", 25)

        p2 = cat_svc.create_product(seller_resp.user_id, ProductCreateRequest(
            title="LuxeErgo Standing Desk",
            slug="luxe-ergo-standing-desk",
            description="Dual motor electric height adjustable standing desk with oak top.",
            category_id=c_home.id,
            brand_id=b_luxe.id,
            price=549.00,
            cost_price=320.00,
            stock_quantity=30,
            images=["https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=600"]
        ))
        inv_svc.add_stock(wh2.id, p2.id, "luxe-ergo-standing-desk", 30)

        print("Database Seeding Completed Successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
