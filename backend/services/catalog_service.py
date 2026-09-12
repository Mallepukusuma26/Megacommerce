"""
MegaCommerce Product Catalog, Category, & Brand Management Domain Service
"""

import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.catalog import Category, Brand, Product, ProductVariant, ProductImage
from database.models.user import SellerProfile, AuditLog
from database.repositories.domain_repositories import ProductRepository, BaseRepository
from shared.enums import ProductStatus, AuditAction
from shared.exceptions import ResourceNotFoundError, AuthorizationError, ValidationCustomError
from shared.dtos import (
    CategoryCreateRequest, CategoryResponse, BrandCreateRequest, BrandResponse,
    ProductCreateRequest, ProductResponse, ProductVariantDTO
)


def slugify(text: str) -> str:
    """Generates clean web-friendly slug from title string."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)


class CatalogService:
    """Core domain service for catalog, category tree, brands, and product moderation."""

    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = BaseRepository(Category, db)
        self.brand_repo = BaseRepository(Brand, db)
        self.variant_repo = BaseRepository(ProductVariant, db)
        self.image_repo = BaseRepository(ProductImage, db)
        self.seller_repo = BaseRepository(SellerProfile, db)
        self.audit_repo = BaseRepository(AuditLog, db)

    def create_category(self, req: CategoryCreateRequest) -> Category:
        """Creates a new catalog category."""
        slug = req.slug or slugify(req.name)
        category = Category(
            name=req.name,
            slug=slug,
            description=req.description,
            parent_id=req.parent_id,
            icon_url=req.icon_url
        )
        self.db.add(category)
        self.db.commit()
        return category

    def list_categories(self) -> List[Category]:
        """Lists active categories."""
        return self.category_repo.get_all()

    def create_brand(self, req: BrandCreateRequest) -> Brand:
        """Creates a new brand."""
        slug = req.slug or slugify(req.name)
        brand = Brand(
            name=req.name,
            slug=slug,
            description=req.description,
            logo_url=req.logo_url
        )
        self.db.add(brand)
        self.db.commit()
        return brand

    def list_brands(self) -> List[Brand]:
        """Lists active brands."""
        return self.brand_repo.get_all()

    def create_product(self, seller_user_id: str, req: ProductCreateRequest) -> Product:
        """Creates a new product listing with variants and images for a seller."""
        # Find seller profile
        seller = self.db.query(SellerProfile).filter(SellerProfile.user_id == seller_user_id).first()
        if not seller:
            raise AuthorizationError("Only registered sellers can create product listings.")

        slug = req.slug or slugify(req.title)
        
        # Check existing slug
        existing = self.product_repo.get_by_slug(slug)
        if existing:
            slug = f"{slug}-{seller.id[:6]}"

        product = Product(
            seller_id=seller.id,
            category_id=req.category_id,
            brand_id=req.brand_id,
            title=req.title,
            slug=slug,
            description=req.description,
            price=req.price,
            discount_price=req.discount_price,
            cost_price=req.cost_price,
            stock_quantity=req.stock_quantity,
            status=ProductStatus.APPROVED.value,  # Auto-approve in dev environment
            attributes=req.attributes or {}
        )
        self.db.add(product)
        self.db.flush()

        # Create Variants
        if req.variants:
            for v in req.variants:
                variant = ProductVariant(
                    product_id=product.id,
                    sku=v.sku,
                    variant_name=v.variant_name,
                    price=v.price,
                    discount_price=v.discount_price,
                    stock_quantity=v.stock_quantity,
                    attributes=v.attributes or {},
                    image_url=v.image_url
                )
                self.db.add(variant)

        # Create Images
        if req.images:
            for idx, img_url in enumerate(req.images):
                img = ProductImage(
                    product_id=product.id,
                    image_url=img_url,
                    is_primary=(idx == 0),
                    sort_order=idx
                )
                self.db.add(img)

        # Audit Log
        audit = AuditLog(
            user_id=seller_user_id,
            action=AuditAction.PRODUCT_CREATE.value,
            entity_name="Product",
            entity_id=product.id,
            details={"title": product.title, "price": product.price}
        )
        self.db.add(audit)
        self.db.commit()
        return product

    def get_product_by_id(self, product_id: str) -> Product:
        """Retrieves product by primary key."""
        return self.product_repo.get_by_id_or_raise(product_id)

    def get_product_by_slug(self, slug: str) -> Product:
        """Retrieves product by web slug."""
        product = self.product_repo.get_by_slug(slug)
        if not product:
            raise ResourceNotFoundError("Product", slug)
        return product

    def filter_products(
        self,
        category_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        """Filters catalog products based on search criteria."""
        return self.product_repo.filter_products(
            category_id=category_id,
            brand_id=brand_id,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            status=ProductStatus.APPROVED.value,
            skip=skip,
            limit=limit
        )

    def approve_product(self, admin_user_id: str, product_id: str) -> Product:
        """Admin product moderation approval workflow."""
        product = self.product_repo.get_by_id_or_raise(product_id)
        product.status = ProductStatus.APPROVED.value
        
        audit = AuditLog(
            user_id=admin_user_id,
            action=AuditAction.PRODUCT_APPROVE.value,
            entity_name="Product",
            entity_id=product.id
        )
        self.db.add(audit)
        self.db.commit()
        return product
