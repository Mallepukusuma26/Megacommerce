"""
MegaCommerce Analytics Core — Customer RFM Segmentation Engine
Calculates Recency, Frequency, and Monetary scores for customer cohort analysis.
"""

from typing import Dict, List, Any, Optional
import datetime


class RFMSegmentationEngine:
    """Calculates customer RFM scores (1 to 5) and assigns loyalty segments."""

    def __init__(self, reference_date: Optional[datetime.datetime] = None):
        self.ref_date = reference_date or datetime.datetime.utcnow()

    def calculate_rfm(self, customer_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Input format: [{'customer_id': str, 'last_order_date': datetime, 'order_count': int, 'total_spent': float}]
        """
        results = []
        for c in customer_data:
            days_since_last = (self.ref_date - c['last_order_date']).days if c['last_order_date'] else 999
            
            # Recency Score
            if days_since_last <= 7: r_score = 5
            elif days_since_last <= 30: r_score = 4
            elif days_since_last <= 90: r_score = 3
            elif days_since_last <= 180: r_score = 2
            else: r_score = 1

            # Frequency Score
            freq = c['order_count']
            if freq >= 15: f_score = 5
            elif freq >= 8: f_score = 4
            elif freq >= 4: f_score = 3
            elif freq >= 2: f_score = 2
            else: f_score = 1

            # Monetary Score
            spent = c['total_spent']
            if spent >= 2500.0: m_score = 5
            elif spent >= 1000.0: m_score = 4
            elif spent >= 400.0: m_score = 3
            elif spent >= 150.0: m_score = 2
            else: m_score = 1

            rfm_score = (r_score * 100) + (f_score * 10) + m_score

            # Segment Rule
            if r_score >= 4 and f_score >= 4 and m_score >= 4:
                segment = "CHAMPIONS"
            elif r_score >= 3 and f_score >= 3:
                segment = "LOYAL_CUSTOMERS"
            elif r_score >= 4 and f_score <= 2:
                segment = "NEW_CUSTOMERS"
            elif r_score <= 2 and f_score >= 3:
                segment = "AT_RISK"
            elif r_score <= 2 and f_score <= 2:
                segment = "HIBERNATING"
            else:
                segment = "REGULAR"

            results.append({
                "customer_id": c["customer_id"],
                "recency_days": days_since_last,
                "frequency_count": freq,
                "monetary_spent": spent,
                "r_score": r_score,
                "f_score": f_score,
                "m_score": m_score,
                "rfm_score": rfm_score,
                "segment": segment
            })

        return results
