"""
MegaCommerce Reviews Core — Moderation & Sentiment Analysis Engine
"""

from typing import Dict, Any, List, Set
import re

PROFANITY_WORD_LIST: Set[str] = {
    "scam", "fraud", "fake", "spam", "garbage", "trash", "terrible", "awful", "horrible"
}


class ReviewModerationAnalyzer:
    """Analyzes customer review text, checks toxicity/profanity, and computes sentiment score."""

    @classmethod
    def analyze_review_text(cls, title: str, comment: str) -> Dict[str, Any]:
        combined = f"{title} {comment}".lower()
        words = re.findall(r'\b[a-z]+\b', combined)

        profanity_hits = [w for w in words if w in PROFANITY_WORD_LIST]
        contains_profanity = len(profanity_hits) > 0

        # Sentiment score calculation
        pos_words = {"great", "excellent", "amazing", "love", "best", "perfect", "good", "fast", "awesome"}
        neg_words = {"bad", "slow", "broken", "worst", "poor", "hate", "refund", "cheap"}

        pos_count = sum([1 for w in words if w in pos_words])
        neg_count = sum([1 for w in words if w in neg_words])

        total_sentiment_words = pos_count + neg_count
        if total_sentiment_words == 0:
            sentiment_score = 0.5  # Neutral
        else:
            sentiment_score = round(pos_count / total_sentiment_words, 2)

        requires_admin_review = contains_profanity or (neg_count > 3)

        return {
            "contains_flagged_keywords": contains_profanity,
            "flagged_words": profanity_hits,
            "sentiment_score": sentiment_score,  # 0.0 (negative) to 1.0 (positive)
            "requires_admin_moderation": requires_admin_review,
            "auto_approve": not requires_admin_review
        }
