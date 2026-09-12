"""
MegaCommerce Order & Checkout REST API Blueprint
"""

from flask import Blueprint, request, jsonify, g
from database.connection import get_db
from backend.services.order_service import OrderService
from backend.middlewares.auth_middleware import require_auth
from shared.dtos import CheckoutRequest
from shared.enums import OrderStatus, UserRole
from shared.exceptions import MegaCommerceException

order_bp = Blueprint("order", __name__, url_prefix="/api/v1/orders")


@order_bp.route("/checkout", methods=["POST"])
@require_auth()
def checkout():
    """POST /api/v1/orders/checkout - Place new order from customer cart."""
    try:
        customer_id = g.current_user["id"]
        data = request.get_json() or {}
        req = CheckoutRequest(**data)
        db = next(get_db())
        service = OrderService(db)
        order = service.checkout_cart(customer_id, req)
        return jsonify({
            "success": True,
            "message": "Order placed successfully.",
            "order_id": order.id,
            "order_number": order.order_number,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "total_amount": order.total_amount
        }), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@order_bp.route("/history", methods=["GET"])
@require_auth()
def get_order_history():
    """GET /api/v1/orders/history - Customer order history list."""
    try:
        customer_id = g.current_user["id"]
        db = next(get_db())
        service = OrderService(db)
        orders = service.order_repo.get_customer_orders(customer_id)
        return jsonify({
            "success": True,
            "count": len(orders),
            "data": [
                {
                    "id": o.id,
                    "order_number": o.order_number,
                    "order_status": o.order_status,
                    "payment_status": o.payment_status,
                    "total_amount": o.total_amount,
                    "created_at": o.created_at.isoformat(),
                    "items_count": len(o.items)
                } for o in orders
            ]
        }), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@order_bp.route("/<string:order_id>/status", methods=["PUT"])
@require_auth(roles=[UserRole.ADMIN, UserRole.SELLER, UserRole.WAREHOUSE_MANAGER])
def update_status(order_id: str):
    """PUT /api/v1/orders/<order_id>/status - Transition order lifecycle state."""
    try:
        user_id = g.current_user["id"]
        data = request.get_json() or {}
        target_status = OrderStatus(data.get("status"))
        notes = data.get("notes")
        db = next(get_db())
        service = OrderService(db)
        order = service.update_order_status(order_id, target_status, changed_by_user_id=user_id, notes=notes)
        return jsonify({
            "success": True,
            "message": f"Order status updated to {order.order_status}."
        }), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
