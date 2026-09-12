"""
MegaCommerce Forecasting Core — Time-Series Moving Average & Exponential Smoothing
Zero External AI API Key Compliance Architecture
"""

from typing import List, Dict, Any
import numpy as np


class ExponentialSmoothingForecaster:
    """Calculates Single & Double Exponential Smoothing for demand series."""

    @staticmethod
    def simple_exponential_smoothing(series: List[float], alpha: float = 0.3, horizon: int = 7) -> List[float]:
        """Calculates Single Exponential Smoothing (SES) for stationary demand."""
        if not series:
            return [0.0] * horizon

        forecasts = [series[0]]
        for t in range(1, len(series)):
            next_val = alpha * series[t] + (1 - alpha) * forecasts[-1]
            forecasts.append(next_val)

        last_forecast = forecasts[-1]
        return [round(float(last_forecast), 2)] * horizon

    @staticmethod
    def double_exponential_smoothing(series: List[float], alpha: float = 0.3, beta: float = 0.1, horizon: int = 7) -> List[float]:
        """Holt's Linear Exponential Smoothing for demand series with trend."""
        if len(series) < 2:
            return [round(float(series[0]), 2)] * horizon if series else [0.0] * horizon

        level = series[0]
        trend = series[1] - series[0]

        for t in range(1, len(series)):
            val = series[t]
            last_level = level
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend

        future = []
        for h in range(1, horizon + 1):
            pred = level + h * trend
            future.append(round(max(0.0, float(pred)), 2))
        return future
