"""
MegaCommerce Recommendations Core — Matrix Factorization & SVD
Zero External AI API Key Compliance Architecture
"""

import numpy as np
from typing import Tuple, List, Dict, Optional


class LocalSVDCollaborativeFiltering:
    """Local Matrix Factorization model for user-product interaction predictions."""

    def __init__(self, num_factors: int = 10, learning_rate: float = 0.01, reg_lambda: float = 0.02):
        self.num_factors = num_factors
        self.lr = learning_rate
        self.reg = reg_lambda
        self.user_factors: Optional[np.ndarray] = None
        self.item_factors: Optional[np.ndarray] = None

    def fit(self, R: np.ndarray, epochs: int = 20) -> None:
        """Fits SVD latent factor matrices on user-item interaction matrix R."""
        num_users, num_items = R.shape
        self.user_factors = np.random.normal(0, 0.1, (num_users, self.num_factors))
        self.item_factors = np.random.normal(0, 0.1, (num_items, self.num_factors))

        non_zero_indices = np.where(R > 0)
        samples = list(zip(non_zero_indices[0], non_zero_indices[1]))

        for epoch in range(epochs):
            np.random.shuffle(samples)
            for u, i in samples:
                prediction = np.dot(self.user_factors[u, :], self.item_factors[i, :])
                err = R[u, i] - prediction

                # Gradient descent updates
                u_f = self.user_factors[u, :]
                i_f = self.item_factors[i, :]

                self.user_factors[u, :] += self.lr * (err * i_f - self.reg * u_f)
                self.item_factors[i, :] += self.lr * (err * u_f - self.reg * i_f)

    def predict(self, user_idx: int, item_idx: int) -> float:
        """Predicts affinity score for user_idx and item_idx."""
        if self.user_factors is None or self.item_factors is None:
            return 0.0
        return float(np.dot(self.user_factors[user_idx, :], self.item_factors[item_idx, :]))
