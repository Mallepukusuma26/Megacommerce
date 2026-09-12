"""
MegaCommerce Authentication REST API Routes Blueprint
"""

from flask import Blueprint, request, jsonify, g
from database.connection import get_db
from backend.services.auth_service import AuthService
from backend.middlewares.auth_middleware import require_auth
from shared.dtos import UserRegisterRequest, UserLoginRequest, AddressCreateRequest
from shared.exceptions import MegaCommerceException

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """POST /api/v1/auth/register - Register customer or seller account."""
    try:
        data = request.get_json() or {}
        req = UserRegisterRequest(**data)
        db = next(get_db())
        service = AuthService(db)
        res = service.register_user(req, ip_address=request.remote_addr)
        return jsonify(res.model_dump()), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /api/v1/auth/login - Authenticate user credentials."""
    try:
        data = request.get_json() or {}
        req = UserLoginRequest(**data)
        db = next(get_db())
        service = AuthService(db)
        res = service.authenticate_user(req, ip_address=request.remote_addr)
        return jsonify(res.model_dump()), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 400


@auth_bp.route("/me", methods=["GET"])
@require_auth()
def get_current_user_profile():
    """GET /api/v1/auth/me - Retrieve current authenticated user profile."""
    try:
        user_id = g.current_user["id"]
        db = next(get_db())
        service = AuthService(db)
        profile = service.get_user_profile(user_id)
        return jsonify({"success": True, "data": profile}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@auth_bp.route("/addresses", methods=["POST"])
@require_auth()
def add_user_address():
    """POST /api/v1/auth/addresses - Add delivery/billing address."""
    try:
        user_id = g.current_user["id"]
        data = request.get_json() or {}
        req = AddressCreateRequest(**data)
        db = next(get_db())
        service = AuthService(db)
        addr = service.add_address(user_id, req)
        return jsonify({
            "success": True,
            "message": "Address added successfully.",
            "address_id": addr.id
        }), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
