"""
MegaCommerce Cart & Wishlist REST API Blueprint
"""

from flask import Blueprint, request, jsonify, g
from database.connection import get_db
from backend.services.cart_service import CartService
from backend.middlewares.auth_middleware import require_auth
from shared.dtos import CartItemAddRequest
from shared.exceptions import MegaCommerceException

cart_bp = Blueprint("cart", __name__, url_prefix="/api/v1/cart")


@cart_bp.route("", methods=["GET"])
@require_auth()
def get_cart_summary():
    """GET /api/v1/cart - Retrieve customer shopping cart breakdown."""
    try:
        user_id = g.current_user["id"]
        db = next(get_db())
        service = CartService(db)
        cart_summary = service.calculate_cart_summary(user_id)
        return jsonify({"success": True, "data": cart_summary.model_dump()}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@cart_bp.route("/items", methods=["POST"])
@require_auth()
def add_to_cart():
    """POST /api/v1/cart/items - Add product to cart."""
    try:
        user_id = g.current_user["id"]
        data = request.get_json() or {}
        req = CartItemAddRequest(**data)
        db = next(get_db())
        service = CartService(db)
        item = service.add_to_cart(user_id, req)
        return jsonify({
            "success": True,
            "message": "Item added to cart.",
            "cart_item_id": item.id
        }), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@cart_bp.route("/items/<string:item_id>", methods=["PUT"])
@require_auth()
def update_cart_item(item_id: str):
    """PUT /api/v1/cart/items/<item_id> - Update item quantity."""
    try:
        user_id = g.current_user["id"]
        data = request.get_json() or {}
        quantity = int(data.get("quantity", 1))
        db = next(get_db())
        service = CartService(db)
        service.update_cart_item_quantity(user_id, item_id, quantity)
        return jsonify({"success": True, "message": "Cart item quantity updated."}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@cart_bp.route("/items/<string:item_id>", methods=["DELETE"])
@require_auth()
def remove_cart_item(item_id: str):
    """DELETE /api/v1/cart/items/<item_id> - Remove item from cart."""
    try:
        user_id = g.current_user["id"]
        db = next(get_db())
        service = CartService(db)
        service.remove_from_cart(user_id, item_id)
        return jsonify({"success": True, "message": "Item removed from cart."}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@cart_bp.route("/coupon", methods=["POST"])
@require_auth()
def apply_coupon():
    """POST /api/v1/cart/coupon - Apply discount coupon to cart."""
    try:
        user_id = g.current_user["id"]
        data = request.get_json() or {}
        code = str(data.get("coupon_code", ""))
        db = next(get_db())
        service = CartService(db)
        service.apply_coupon(user_id, code)
        return jsonify({"success": True, "message": f"Coupon '{code}' applied successfully."}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
