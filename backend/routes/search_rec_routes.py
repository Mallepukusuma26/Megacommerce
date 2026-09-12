"""
MegaCommerce Search Engine & ML Recommendation REST API Blueprint
"""

from flask import Blueprint, request, jsonify
from database.connection import get_db
from ml_services.search_engine import LocalSearchEngine
from ml_services.recommendation_engine import LocalRecommendationEngine
from shared.dtos import SearchRequest
from shared.exceptions import MegaCommerceException

search_rec_bp = Blueprint("search_rec", __name__, url_prefix="/api/v1")


@search_rec_bp.route("/search/query", methods=["POST"])
def search_catalog():
    """POST /api/v1/search/query - Local Vector & TF-IDF search matching."""
    try:
        data = request.get_json() or {}
        req = SearchRequest(**data)
        db = next(get_db())
        engine = LocalSearchEngine(db)
        results = engine.search(req)
        return jsonify({
            "success": True,
            "query": req.query,
            "count": len(results),
            "data": results
        }), 200
    except MegaCommerceException as err:
        return jsonify(err.to_dict()), err.status_code


@search_rec_bp.route("/search/suggestions", methods=["GET"])
def search_suggestions():
    """GET /api/v1/search/suggestions?q=... - Search auto-complete suggestions."""
    q = request.args.get("q", "")
    db = next(get_db())
    engine = LocalSearchEngine(db)
    suggestions = engine.get_search_suggestions(q)
    return jsonify({"success": True, "data": suggestions}), 200


@search_rec_bp.route("/recommendations/similar/<string:product_id>", methods=["GET"])
def get_similar_recommendations(product_id: str):
    """GET /api/v1/recommendations/similar/<product_id> - Content-based similar items."""
    db = next(get_db())
    engine = LocalRecommendationEngine(db)
    recs = engine.get_similar_products(product_id)
    return jsonify({"success": True, "count": len(recs), "data": recs}), 200


@search_rec_bp.route("/recommendations/popular", methods=["GET"])
def get_popular_recommendations():
    """GET /api/v1/recommendations/popular - Trending product recommendations."""
    db = next(get_db())
    engine = LocalRecommendationEngine(db)
    recs = engine.get_popular_products()
    return jsonify({"success": True, "count": len(recs), "data": recs}), 200
