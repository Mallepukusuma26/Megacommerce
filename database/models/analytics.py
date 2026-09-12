"""
MegaCommerce AI/ML & Platform Analytics Database Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Float, Integer, JSON
from database.connection import Base
from shared.enums import FraudRiskCategory


def generate_uuid() -> str:
    return str(uuid.uuid4())


class FraudEvent(Base):
    __tablename__ = "fraud_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False, index=True)
    risk_category = Column(String(50), nullable=False, default=FraudRiskCategory.LOW.value, index=True)
    flagged = Column(Boolean, default=False, nullable=False)
    detection_reasons = Column(JSON, nullable=False, default=list)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted_demand_units = Column(Integer, nullable=False)
    confidence_lower = Column(Float, nullable=False)
    confidence_upper = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False, default="ARIMA-XGB-v1")
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SalesPrediction(Base):
    __tablename__ = "sales_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    target_type = Column(String(50), nullable=False)  # PLATFORM, SELLER, CATEGORY, PRODUCT
    target_id = Column(String(36), nullable=False, index=True)
    prediction_period = Column(String(50), nullable=False)  # DAILY, WEEKLY, MONTHLY
    target_date = Column(DateTime, nullable=False, index=True)
    predicted_revenue = Column(Float, nullable=False)
    predicted_order_count = Column(Integer, nullable=False)
    trend_direction = Column(String(20), nullable=False, default="UPWARD")
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CustomerAnalyticsSummary(Base):
    __tablename__ = "customer_analytics_summaries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_orders_placed = Column(Integer, default=0, nullable=False)
    total_amount_spent = Column(Float, default=0.0, nullable=False)
    average_order_value = Column(Float, default=0.0, nullable=False)
    favorite_category_id = Column(String(36), nullable=True)
    customer_segment = Column(String(50), default="REGULAR", nullable=False)  # NEW, REGULAR, VIP, AT_RISK
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SellerAnalyticsSummary(Base):
    __tablename__ = "seller_analytics_summaries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    seller_id = Column(String(36), ForeignKey("seller_profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_orders_received = Column(Integer, default=0, nullable=False)
    total_revenue_earned = Column(Float, default=0.0, nullable=False)
    return_rate_percentage = Column(Float, default=0.0, nullable=False)
    inventory_turnover_ratio = Column(Float, default=0.0, nullable=False)
    seller_tier = Column(String(50), default="SILVER", nullable=False)  # BRONZE, SILVER, GOLD, PLATINUM
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
