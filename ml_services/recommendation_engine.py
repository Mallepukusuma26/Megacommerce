"""
MegaCommerce Local Recommendation Engine
Zero External AI API Key Compliance Architecture
Hybrid Content-Based & Collaborative Filtering Machine Learning Engine
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database.models.catalog import Product
from database.models.order import Order, OrderItem
from database.models.reviews import Review


class LocalRecommendationEngine:
    """Local Hybrid Recommendation Machine Learning Engine."""

    def __init__(self, db: Session):
        self.db = db

    def get_similar_products(self, product_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Content-Based Recommendation using product feature TF-IDF vector similarity."""
        target_prod = self.db.query(Product).filter(Product.id == product_id).first()
        if not target_prod:
            return []

        all_products = self.db.query(Product).filter(Product.status == "APPROVED").all()
        if len(all_products) <= 1:
            return []

        corpus = []
        prod_ids = []

        for p in all_products:
            doc = f"{p.title} {p.category.name if p.category else ''} {p.description}"
            corpus.append(doc)
            prod_ids.append(p.id)

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus)

        try:
            target_idx = prod_ids.index(product_id)
        except ValueError:
            return []

        sims = cosine_similarity(matrix[target_idx:target_idx+1], matrix).flatten()
        top_indices = np.argsort(sims)[::-1]

        recs = []
        for idx in top_indices:
            pid = prod_ids[idx]
            if pid == product_id:
                continue

            p = self.db.query(Product).filter(Product.id == pid).first()
            if p:
                recs.append({
                    "product_id": p.id,
                    "title": p.title,
                    "slug": p.slug,
                    "price": p.price,
                    "rating_average": p.rating_average,
                    "similarity_score": round(float(sims[idx]), 4),
                    "primary_image": p.images[0].image_url if p.images else None
                })
            if len(recs) >= limit:
                break
        return recs

    def get_frequently_bought_together(self, product_id: str, limit: int = 4) -> List[Dict[str, Any]]:
        """Order co-occurrence matrix recommendation."""
        # Find orders containing target_product_id
        order_ids_stmt = self.db.query(OrderItem.order_id).filter(OrderItem.product_id == product_id).subquery()
        
        # Find co-occurring items in those orders
        co_items = (
            self.db.query(OrderItem.product_id, func.count(OrderItem.id).label("co_count"))
            .filter(OrderItem.order_id.in_(order_ids_stmt), OrderItem.product_id != product_id)
            .group_by(OrderItem.product_id)
            .order_by(desc("co_count"))
            .limit(limit)
            .all()
        )

        recs = []
        for pid, count in co_items:
            p = self.db.query(Product).filter(Product.id == pid).first()
            if p:
                recs.append({
                    "product_id": p.id,
                    "title": p.title,
                    "slug": p.slug,
                    "price": p.price,
                    "co_occurrence_count": count,
                    "primary_image": p.images[0].image_url if p.images else None
                })
        return recs

    def get_popular_products(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Trending and top-rated products fallback recommendation."""
        products = (
            self.db.query(Product)
            .filter(Product.status == "APPROVED")
            .order_by(desc(Product.rating_average), desc(Product.review_count))
            .limit(limit)
            .all()
        )

        return [
            {
                "product_id": p.id,
                "title": p.title,
                "slug": p.slug,
                "price": p.price,
                "discount_price": p.discount_price,
                "rating_average": p.rating_average,
                "primary_image": p.images[0].image_url if p.images else None
            } for p in products
        ]
