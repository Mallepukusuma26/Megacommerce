"""
MegaCommerce Product Review & Rating Management Service
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models.reviews import Review, ReviewReport
from database.models.catalog import Product
from database.models.order import Order, OrderItem
from database.models.user import User, AuditLog
from database.repositories.domain_repositories import BaseRepository
from packages.reviews_moderation.review_analyzer import ReviewModerationAnalyzer
from shared.exceptions import ResourceNotFoundError, AuthorizationError


class ProductReviewService:
    """Core domain service for product reviews, ratings, and moderation."""

    def __init__(self, db: Session):
        self.db = db
        self.review_repo = BaseRepository(Review, db)

    def submit_review(self, customer_id: str, product_id: str, rating: int, title: str, comment: str) -> Review:
        """Customer submits review for a product with sentiment moderation analysis."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ResourceNotFoundError("Product", product_id)

        if rating < 1 or rating > 5:
            rating = max(1, min(5, rating))

        # Verified purchase check
        verified = (
            self.db.query(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.customer_id == customer_id, OrderItem.product_id == product_id, Order.order_status == "DELIVERED")
            .first()
        ) is not None

        # Sentiment & Profanity Analysis
        analysis = ReviewModerationAnalyzer.analyze_review_text(title, comment)

        review = Review(
            product_id=product_id,
            customer_id=customer_id,
            rating=rating,
            title=title,
            comment=comment,
            is_verified_purchase=verified,
            is_approved=analysis["auto_approve"]
        )
        self.db.add(review)
        self.db.flush()

        # Update product aggregate rating
        self._recalculate_product_rating(product_id)
        self.db.commit()
        return review

    def _recalculate_product_rating(self, product_id: str) -> None:
        reviews = self.db.query(Review).filter(Review.product_id == product_id, Review.is_approved == True).all()
        if not reviews:
            return

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.review_count = len(reviews)
            product.rating_average = round(sum([r.rating for r in reviews]) / len(reviews), 2)

    def get_product_reviews(self, product_id: str, skip: int = 0, limit: int = 10) -> List[Review]:
        return (
            self.db.query(Review)
            .filter(Review.product_id == product_id, Review.is_approved == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
