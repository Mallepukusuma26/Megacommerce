"""
MegaCommerce Advanced ML, Finance, Invoicing, & Returns REST API Blueprint
"""

from flask import Blueprint, request, jsonify, send_file, g
from database.connection import get_db
from backend.services.invoice_service import LocalInvoiceService
from backend.services.returns_refunds_service import ReturnsRefundsService
from ml_services.fraud_detector import LocalFraudDetector
from ml_services.demand_forecaster import LocalDemandForecaster
from ml_services.sales_predictor import LocalSalesPredictor
from backend.middlewares.auth_middleware import require_auth
from shared.enums import UserRole, ReturnReason
from shared.exceptions import MegaCommerceException

adv_bp = Blueprint("advanced", __name__, url_prefix="/api/v1")


@adv_bp.route("/invoices/<string:order_id>/pdf", methods=["GET"])
@require_auth()
def download_invoice_pdf(order_id: str):
    """GET /api/v1/invoices/<order_id>/pdf - Download generated ReportLab PDF invoice."""
    try:
        db = next(get_db())
        service = LocalInvoiceService(db)
        pdf_path = service.generate_pdf_invoice(order_id)
        return send_file(str(pdf_path), mimetype="application/pdf", as_attachment=True)
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@adv_bp.route("/returns/request", methods=["POST"])
@require_auth()
def request_return():
    """POST /api/v1/returns/request - Customer submits return request."""
    try:
        user_id = g.current_user["id"]
        data = request.get_json() or {}
        order_id = str(data.get("order_id"))
        reason = ReturnReason(data.get("reason", "DEFECTIVE"))
        details = str(data.get("details", ""))
        
        db = next(get_db())
        service = ReturnsRefundsService(db)
        ret_req = service.create_return_request(user_id, order_id, reason, details)
        return jsonify({
            "success": True,
            "message": "Return request submitted.",
            "return_request_id": ret_req.id
        }), 201
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@adv_bp.route("/fraud/assess/<string:order_id>", methods=["GET"])
@require_auth(roles=[UserRole.ADMIN])
def assess_fraud(order_id: str):
    """GET /api/v1/fraud/assess/<order_id> - Admin fraud anomaly risk evaluation."""
    try:
        db = next(get_db())
        detector = LocalFraudDetector(db)
        res = detector.evaluate_order_risk(order_id)
        return jsonify({"success": True, "data": res.model_dump()}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@adv_bp.route("/analytics/forecast/demand/<string:product_id>", methods=["GET"])
@require_auth(roles=[UserRole.SELLER, UserRole.ADMIN])
def forecast_demand(product_id: str):
    """GET /api/v1/analytics/forecast/demand/<product_id> - Time-series demand forecast."""
    try:
        db = next(get_db())
        forecaster = LocalDemandForecaster(db)
        res = forecaster.forecast_product_demand(product_id)
        return jsonify({"success": True, "data": res}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@adv_bp.route("/analytics/predictions/sales", methods=["GET"])
@require_auth(roles=[UserRole.ADMIN])
def predict_sales():
    """GET /api/v1/analytics/predictions/sales - Platform monthly revenue predictions."""
    try:
        db = next(get_db())
        predictor = LocalSalesPredictor(db)
        res = predictor.predict_platform_monthly_revenue()
        return jsonify({"success": True, "data": res}), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code
