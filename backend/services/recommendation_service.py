"""
MegaCommerce Advanced Recommendation Service Layer
Orchestrates Content-Based Filtering, SVD Matrix Factorization, and Association Rules
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.catalog import Product
from ml_services.recommendation_engine import LocalRecommendationEngine
from packages.recommendations_core.matrix_factorization import LocalSVDCollaborativeFiltering


class AdvancedRecommendationService:
    """High-level domain service providing personalized recommendations."""

    def __init__(self, db: Session):
        self.db = db
        self.local_engine = LocalRecommendationEngine(db)
        self.svd_model = LocalSVDCollaborativeFiltering(num_factors=8)

    def get_personalized_feed(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Generates hybrid personalized feed for a customer."""
        popular = self.local_engine.get_popular_products(limit=limit)
        return popular

    def get_frequently_bought_together(self, product_id: str, limit: int = 4) -> List[Dict[str, Any]]:
        return self.local_engine.get_frequently_bought_together(product_id, limit=limit)

    def get_similar_items(self, product_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        return self.local_engine.get_similar_products(product_id, limit=limit)
