"""
MegaCommerce Domain Packages Unit Test Suite
"""

import datetime
import numpy as np
from packages.search_core.tokenizer import tokenize, generate_ngrams
from packages.recommendations_core.matrix_factorization import LocalSVDCollaborativeFiltering
from packages.analytics_engine.rfm_segmentation import RFMSegmentationEngine


def test_search_tokenizer_and_ngrams():
    text = "The Wireless Noise Cancelling Headphones 2026!"
    tokens = tokenize(text)
    assert "wireless" in tokens
    assert "headphones" in tokens
    assert "the" not in tokens  # Stop word removed

    ngrams = generate_ngrams(tokens, n=2)
    assert len(ngrams) >= 1
    assert "wireless noise" in ngrams or "noise cancelling" in ngrams


def test_svd_matrix_factorization_training():
    R = np.array([
        [5, 3, 0, 1],
        [4, 0, 0, 1],
        [1, 1, 0, 5],
        [1, 0, 0, 4],
        [0, 1, 5, 4],
    ])
    model = LocalSVDCollaborativeFiltering(num_factors=3)
    model.fit(R, epochs=10)

    pred = model.predict(0, 0)
    assert isinstance(pred, float)


def test_rfm_customer_segmentation():
    now = datetime.datetime.utcnow()
    customers = [
        {"customer_id": "CUST-001", "last_order_date": now - datetime.timedelta(days=2), "order_count": 10, "total_spent": 3000.0},
        {"customer_id": "CUST-002", "last_order_date": now - datetime.timedelta(days=120), "order_count": 1, "total_spent": 50.0}
    ]

    engine = RFMSegmentationEngine(reference_date=now)
    res = engine.calculate_rfm(customers)
    assert len(res) == 2
    assert res[0]["segment"] == "CHAMPIONS"
    assert res[1]["segment"] in ["HIBERNATING", "AT_RISK"]


def test_payment_simulators_package():
    from packages.payment_sim.gateways import SimulatedCardGateway, SimulatedUPIGateway, SimulatedCODGateway
    card_res = SimulatedCardGateway.process_card("4111111111114242", "12/28", "123", 150.00)
    assert card_res["status"] == "SUCCESS"
    assert card_res["last4"] == "4242"

    upi_res = SimulatedUPIGateway.process_upi("test@upi", 99.00)
    assert upi_res["status"] == "SUCCESS"

    cod_res = SimulatedCODGateway.process_cod("ORD-100", 250.00)
    assert cod_res["status"] == "PENDING_COLLECTION_ON_DELIVERY"


def test_delivery_route_planner_package():
    from packages.delivery_sim.route_planner import LocalRoutePlanner
    dist = LocalRoutePlanner.calculate_haversine_distance("Seattle", "Boston")
    assert dist > 2000.0  # Transcontinental distance in miles

    hours = LocalRoutePlanner.estimate_transit_time_hours("Seattle", "San Jose")
    assert hours > 0.0


def test_time_series_forecasting_package():
    from packages.forecasting_engine.time_series import ExponentialSmoothingForecaster
    series = [10.0, 12.0, 15.0, 18.0, 22.0, 25.0]
    forecast = ExponentialSmoothingForecaster.double_exponential_smoothing(series, horizon=5)
    assert len(forecast) == 5
    assert forecast[0] >= 25.0  # Upward trend prediction

