"""
MegaCommerce Local Time-Series Demand Forecasting Pipeline
Zero External AI API Key Compliance Architecture
Powered by Python NumPy, Scipy & Ridge Regression
"""

import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.linear_model import Ridge
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models.order import OrderItem, Order
from database.models.catalog import Product
from database.models.analytics import DemandForecast


class LocalDemandForecaster:
    """Local Statistical Time-Series Demand Forecaster."""

    def __init__(self, db: Session):
        self.db = db

    def forecast_product_demand(self, product_id: str, horizon_days: int = 30) -> Dict[str, Any]:
        """Projects future 30-day unit demand based on historical order history."""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": True, "message": "Product not found"}

        # Fetch historical daily sales
        items = (
            self.db.query(OrderItem.quantity, Order.created_at)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(OrderItem.product_id == product_id)
            .all()
        )

        daily_units = {}
        for qty, created_at in items:
            day_str = created_at.strftime("%Y-%m-%d")
            daily_units[day_str] = daily_units.get(day_str, 0) + qty

        # Prepare X and Y for regression
        X, Y = [], []
        today = datetime.datetime.utcnow().date()
        
        # Build 30-day historical window
        for i in range(30, 0, -1):
            d = today - datetime.timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            X.append([30 - i])
            Y.append(daily_units.get(d_str, max(1, product.stock_quantity // 10)))

        X = np.array(X)
        Y = np.array(Y)

        model = Ridge(alpha=1.0)
        model.fit(X, Y)

        # Forecast future days
        future_X = np.array([[30 + i] for i in range(1, horizon_days + 1)])
        predictions = model.predict(future_X)
        predictions = np.maximum(0, predictions)  # No negative demand

        total_predicted = int(np.sum(predictions))
        daily_forecasts = []

        for i, pred_units in enumerate(predictions):
            f_date = today + datetime.timedelta(days=i+1)
            pred_val = int(round(pred_units))
            lower_bound = max(0, int(round(pred_units * 0.8)))
            upper_bound = int(round(pred_units * 1.25))

            daily_forecasts.append({
                "date": f_date.strftime("%Y-%m-%d"),
                "predicted_units": pred_val,
                "confidence_lower": lower_bound,
                "confidence_upper": upper_bound
            })

            # Save DemandForecast record
            df_rec = DemandForecast(
                product_id=product_id,
                sku=product.slug,
                forecast_date=f_date,
                predicted_demand_units=pred_val,
                confidence_lower=float(lower_bound),
                confidence_upper=float(upper_bound),
                model_version="Ridge-TS-v1"
            )
            self.db.add(df_rec)

        self.db.commit()

        return {
            "product_id": product_id,
            "sku": product.slug,
            "horizon_days": horizon_days,
            "total_predicted_demand_units": total_predicted,
            "reorder_recommended": (total_predicted > product.stock_quantity),
            "suggested_reorder_quantity": max(0, total_predicted - product.stock_quantity + 20),
            "daily_forecasts": daily_forecasts
        }
