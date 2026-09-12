"""
MegaCommerce Product Catalog REST API Routes Blueprint
"""

from flask import Blueprint, request, jsonify, g
from database.connection import get_db
from backend.services.catalog_service import CatalogService
from backend.middlewares.auth_middleware import require_auth
from shared.enums import UserRole
from shared.dtos import CategoryCreateRequest, BrandCreateRequest, ProductCreateRequest
from shared.exceptions import MegaCommerceException

catalog_bp = Blueprint("catalog", __name__, url_prefix="/api/v1/catalog")


@catalog_bp.route("/categories", methods=["GET"])
def list_categories():
    """GET /api/v1/catalog/categories - List all active categories."""
    db = next(get_db())
    service = CatalogService(db)
    categories = service.list_categories()
    return jsonify({
        "success": True,
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "parent_id": c.parent_id,
                "icon_url": c.icon_url
            } for c in categories
        ]
    }), 200


@catalog_bp.route("/categories", methods=["POST"])
@require_auth(roles=[UserRole.ADMIN])
def create_category():
    """POST /api/v1/catalog/categories - Create new category (Admin only)."""
    try:
        data = request.get_json() or {}
        req = CategoryCreateRequest(**data)
        db = next(get_db())
        service = CatalogService(db)
        cat = service.create_category(req)
        return jsonify({
            "success": True,
            "message": "Category created successfully.",
            "category_id": cat.id
        }), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@catalog_bp.route("/brands", methods=["GET"])
def list_brands():
    """GET /api/v1/catalog/brands - List all brands."""
    db = next(get_db())
    service = CatalogService(db)
    brands = service.list_brands()
    return jsonify({
        "success": True,
        "data": [
            {"id": b.id, "name": b.name, "slug": b.slug, "logo_url": b.logo_url}
            for b in brands
        ]
    }), 200


@catalog_bp.route("/brands", methods=["POST"])
@require_auth(roles=[UserRole.ADMIN])
def create_brand():
    """POST /api/v1/catalog/brands - Create brand (Admin only)."""
    try:
        data = request.get_json() or {}
        req = BrandCreateRequest(**data)
        db = next(get_db())
        service = CatalogService(db)
        b = service.create_brand(req)
        return jsonify({
            "success": True,
            "message": "Brand created successfully.",
            "brand_id": b.id
        }), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@catalog_bp.route("/products", methods=["POST"])
@require_auth(roles=[UserRole.SELLER, UserRole.ADMIN])
def create_product():
    """POST /api/v1/catalog/products - Seller creates product listing."""
    try:
        seller_user_id = g.current_user["id"]
        data = request.get_json() or {}
        req = ProductCreateRequest(**data)
        db = next(get_db())
        service = CatalogService(db)
        product = service.create_product(seller_user_id, req)
        return jsonify({
            "success": True,
            "message": "Product created successfully.",
            "product_id": product.id,
            "slug": product.slug
        }), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@catalog_bp.route("/products", methods=["GET"])
def get_products():
    """GET /api/v1/catalog/products - Browse and filter catalog products."""
    try:
        category_id = request.args.get("category_id")
        brand_id = request.args.get("brand_id")
        min_price = float(request.args.get("min_price")) if request.args.get("min_price") else None
        max_price = float(request.args.get("max_price")) if request.args.get("max_price") else None
        min_rating = float(request.args.get("min_rating")) if request.args.get("min_rating") else None
        skip = int(request.args.get("skip", 0))
        limit = int(request.args.get("limit", 20))

        db = next(get_db())
        service = CatalogService(db)
        products = service.filter_products(
            category_id=category_id,
            brand_id=brand_id,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            skip=skip,
            limit=limit
        )

        return jsonify({
            "success": True,
            "count": len(products),
            "data": [
                {
                    "id": p.id,
                    "title": p.title,
                    "slug": p.slug,
                    "price": p.price,
                    "discount_price": p.discount_price,
                    "stock_quantity": p.stock_quantity,
                    "rating_average": p.rating_average,
                    "review_count": p.review_count,
                    "category_id": p.category_id,
                    "brand_id": p.brand_id,
                    "primary_image": p.images[0].image_url if p.images else None
                } for p in products
            ]
        }), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@catalog_bp.route("/products/<string:product_id_or_slug>", methods=["GET"])
def get_product_details(product_id_or_slug: str):
    """GET /api/v1/catalog/products/<id_or_slug> - Product detail view."""
    try:
        db = next(get_db())
        service = CatalogService(db)
        try:
            product = service.get_product_by_id(product_id_or_slug)
        except Exception:
            product = service.get_product_by_slug(product_id_or_slug)

        return jsonify({
            "success": True,
            "data": {
                "id": product.id,
                "title": product.title,
                "slug": product.slug,
                "description": product.description,
                "price": product.price,
                "discount_price": product.discount_price,
                "stock_quantity": product.stock_quantity,
                "rating_average": product.rating_average,
                "review_count": product.review_count,
                "category_id": product.category_id,
                "brand_id": product.brand_id,
                "seller_id": product.seller_id,
                "attributes": product.attributes,
                "variants": [
                    {
                        "id": v.id,
                        "sku": v.sku,
                        "name": v.variant_name,
                        "price": v.price,
                        "stock_quantity": v.stock_quantity,
                        "image_url": v.image_url
                    } for v in product.variants
                ],
                "images": [img.image_url for img in product.images]
            }
        }), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
