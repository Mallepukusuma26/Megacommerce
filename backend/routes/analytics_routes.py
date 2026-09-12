"""
MegaCommerce Analytics REST API Blueprint
"""

from flask import Blueprint, request, jsonify, g
from database.connection import get_db
from backend.services.analytics_service import AnalyticsService
from backend.middlewares.auth_middleware import require_auth
from shared.enums import UserRole
from shared.exceptions import MegaCommerceException

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


@analytics_bp.route("/customer", methods=["GET"])
@require_auth(roles=[UserRole.CUSTOMER, UserRole.ADMIN])
def get_customer_analytics():
    """GET /api/v1/analytics/customer - Customer portal spending dashboard."""
    try:
        user_id = g.current_user["id"]
        db = next(get_db())
        service = AnalyticsService(db)
        data = service.get_customer_analytics(user_id)
        return jsonify({"success": True, "data": data}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@analytics_bp.route("/seller", methods=["GET"])
@require_auth(roles=[UserRole.SELLER, UserRole.ADMIN])
def get_seller_analytics():
    """GET /api/v1/analytics/seller - Seller portal revenue dashboard."""
    try:
        user_id = g.current_user["id"]
        db = next(get_db())
        service = AnalyticsService(db)
        data = service.get_seller_analytics(user_id)
        return jsonify({"success": True, "data": data}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@analytics_bp.route("/admin", methods=["GET"])
@require_auth(roles=[UserRole.ADMIN])
def get_admin_analytics():
    """GET /api/v1/analytics/admin - Platform admin overview dashboard."""
    try:
        db = next(get_db())
        service = AnalyticsService(db)
        data = service.get_platform_admin_analytics()
        return jsonify({"success": True, "data": data}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
