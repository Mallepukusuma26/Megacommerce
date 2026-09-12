"""
MegaCommerce Ecosystem Master Application Server
Zero External API Key Compliance Architecture
"""

import os
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from config.settings import settings
from database.connection import init_db
from backend.routes.auth_routes import auth_bp
from backend.routes.catalog_routes import catalog_bp
from backend.routes.cart_routes import cart_bp
from backend.routes.order_routes import order_bp
from backend.routes.search_rec_routes import search_rec_bp
from backend.routes.advanced_services_routes import adv_bp
from backend.routes.analytics_routes import analytics_bp


def create_app() -> Flask:
    """Application Factory initializing Flask app instance, CORS, DB models, and REST routes."""
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static"
    )

    # Enable CORS
    CORS(app, origins=settings.security.CORS_ALLOWED_ORIGINS)

    # Initialize DB Schemas
    init_db()

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(search_rec_bp)
    app.register_blueprint(adv_bp)
    app.register_blueprint(analytics_bp)

    # Core SPA Route Handler
    @app.route("/")
    @app.route("/register")
    @app.route("/login")
    @app.route("/customer")
    @app.route("/customer/<path:subpath>")
    @app.route("/seller")
    @app.route("/seller/<path:subpath>")
    @app.route("/admin")
    @app.route("/admin/<path:subpath>")
    def index(subpath=None):
        """Serves main Web SPA frontend for all application routes."""
        return render_template("index.html")

    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return {
            "status": "HEALTHY",
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "api_keys_required": 0
        }, 200

    return app


app = create_app()

if __name__ == "__main__":
    print(f"Starting {settings.PROJECT_NAME} on http://{settings.HOST}:{settings.PORT}")
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
