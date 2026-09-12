"""
MegaCommerce Dynamic Pricing & Tax Matrix Calculation Engine
Zero External API Key Compliance Architecture
"""

from typing import Dict, Any, List, Optional
import datetime


# State Tax Rates Table (Simulated 50 States)
US_STATE_TAX_RATES: Dict[str, float] = {
    "AL": 0.040, "AK": 0.000, "AZ": 0.056, "AR": 0.065, "CA": 0.0725,
    "CO": 0.029, "CT": 0.0635, "DE": 0.000, "FL": 0.060, "GA": 0.040,
    "HI": 0.040, "ID": 0.060, "IL": 0.0625, "IN": 0.070, "IA": 0.060,
    "KS": 0.065, "KY": 0.060, "LA": 0.0445, "ME": 0.055, "MD": 0.060,
    "MA": 0.0625, "MI": 0.060, "MN": 0.06875, "MS": 0.070, "MO": 0.04225,
    "MT": 0.000, "NE": 0.055, "NV": 0.0685, "NH": 0.000, "NJ": 0.06625,
    "NM": 0.05125, "NY": 0.040, "NC": 0.0475, "ND": 0.050, "OH": 0.0575,
    "OK": 0.045, "OR": 0.000, "PA": 0.060, "RI": 0.070, "SC": 0.060,
    "SD": 0.045, "TN": 0.070, "TX": 0.0625, "UT": 0.061, "VT": 0.060,
    "VA": 0.053, "WA": 0.065, "WV": 0.060, "WI": 0.050, "WY": 0.040
}


class StateTaxCalculator:
    """Calculates US State Sales Tax based on delivery destination."""

    @staticmethod
    def get_tax_rate(state_code: str) -> float:
        return US_STATE_TAX_RATES.get(state_code.upper().strip(), 0.08)

    @classmethod
    def calculate_sales_tax(cls, taxable_amount: float, state_code: str) -> float:
        rate = cls.get_tax_rate(state_code)
        return round(taxable_amount * rate, 2)


class TieredVolumeDiscountEngine:
    """Calculates bulk quantity tier discounts for wholesale & B2B orders."""

    @staticmethod
    def calculate_volume_discount(unit_price: float, quantity: int) -> float:
        """
        Quantity Tiers:
        1 - 4: 0% discount
        5 - 9: 5% discount
        10 - 24: 10% discount
        25 - 49: 15% discount
        50+: 20% discount
        """
        if quantity >= 50:
            discount_pct = 0.20
        elif quantity >= 25:
            discount_pct = 0.15
        elif quantity >= 10:
            discount_pct = 0.10
        elif quantity >= 5:
            discount_pct = 0.05
        else:
            discount_pct = 0.00

        discounted_unit_price = unit_price * (1.0 - discount_pct)
        return round(discounted_unit_price, 2)


class ProfitMarginAnalyzer:
    """Computes gross profit, margin percentage, and markup percentage."""

    @staticmethod
    def calculate_profit_metrics(selling_price: float, cost_price: float) -> Dict[str, float]:
        gross_profit = selling_price - cost_price
        margin_pct = (gross_profit / selling_price * 100.0) if selling_price > 0 else 0.0
        markup_pct = (gross_profit / cost_price * 100.0) if cost_price > 0 else 0.0

        return {
            "selling_price": round(selling_price, 2),
            "cost_price": round(cost_price, 2),
            "gross_profit": round(gross_profit, 2),
            "margin_percentage": round(margin_pct, 2),
            "markup_percentage": round(markup_pct, 2)
        }
