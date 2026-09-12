"""
MegaCommerce Local Vector & TF-IDF Search Engine
Zero External Search API Key Compliance Architecture
Built with Python NumPy, Scikit-Learn (CountVectorizer, TfidfTransformer), and Cosine Similarity
"""

import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from database.models.catalog import Product, Category, Brand
from shared.dtos import SearchRequest


def normalize_text(text: str) -> str:
    """Normalizes raw input text (lowercasing, punctuation stripping)."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text)


class LocalSearchEngine:
    """Local In-Memory Vector Search Engine powered by TF-IDF & Cosine Similarity."""

    def __init__(self, db: Session):
        self.db = db
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._fitted = False
        self._product_ids: List[str] = []
        self._tfidf_matrix = None

    def build_index(self) -> None:
        """Constructs TF-IDF vector index across catalog titles, descriptions, and attributes."""
        products = self.db.query(Product).filter(Product.status == "APPROVED").all()
        if not products:
            self._fitted = False
            return

        corpus = []
        self._product_ids = []

        for p in products:
            cat_name = p.category.name if p.category else ""
            brand_name = p.brand.name if p.brand else ""
            doc = f"{p.title} {p.title} {cat_name} {brand_name} {p.description}"
            corpus.append(normalize_text(doc))
            self._product_ids.append(p.id)

        self._tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self._fitted = True

    def search(self, req: SearchRequest) -> List[Dict[str, Any]]:
        """Executes full-text query matching, relevance ranking, and faceted filtering."""
        query_text = normalize_text(req.query)
        if not self._fitted or self._tfidf_matrix is None:
            self.build_index()

        if not self._fitted or self._tfidf_matrix is None:
            return []

        # Vectorize Search Query
        query_vector = self.vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vector, self._tfidf_matrix).flatten()

        # Rank by score
        top_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            # Basic threshold or keyword match
            if score <= 0.05 and len(query_text) > 2:
                continue

            product_id = self._product_ids[idx]
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                continue

            # Apply Facet Filters
            if req.category_id and product.category_id != req.category_id:
                continue
            if req.brand_id and product.brand_id != req.brand_id:
                continue
            if req.min_price is not None and product.price < req.min_price:
                continue
            if req.max_price is not None and product.price > req.max_price:
                continue
            if req.min_rating is not None and product.rating_average < req.min_rating:
                continue

            results.append({
                "product_id": product.id,
                "title": product.title,
                "slug": product.slug,
                "price": product.price,
                "discount_price": product.discount_price,
                "rating_average": product.rating_average,
                "review_count": product.review_count,
                "category_id": product.category_id,
                "relevance_score": round(score, 4),
                "primary_image": product.images[0].image_url if product.images else None
            })

        # Sorting
        if req.sort_by == "price_low":
            results.sort(key=lambda x: x["price"])
        elif req.sort_by == "price_high":
            results.sort(key=lambda x: x["price"], reverse=True)
        elif req.sort_by == "rating":
            results.sort(key=lambda x: x["rating_average"], reverse=True)

        return results

    def get_search_suggestions(self, query_prefix: str, limit: int = 5) -> List[str]:
        """Provides auto-complete search query suggestions."""
        prefix = normalize_text(query_prefix)
        if len(prefix) < 2:
            return []

        suggestions = set()
        products = self.db.query(Product).filter(Product.status == "APPROVED").all()
        for p in products:
            if prefix in p.title.lower():
                suggestions.add(p.title)
            if len(suggestions) >= limit:
                break
        return list(suggestions)
