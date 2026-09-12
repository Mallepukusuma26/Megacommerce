"""
MegaCommerce Application Configuration & System Settings
Zero External API Key Compliance Architecture
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class DatabaseConfig:
    """Database Connection & Pool Settings"""
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")
    DB_NAME: str = os.getenv("DB_NAME", "megacommerce.db")
    SQLITE_PATH: Path = BASE_DIR / "data" / "megacommerce.db"
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "megacommerce")
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 10
    ECHO_SQL: bool = os.getenv("ECHO_SQL", "False").lower() in ("true", "1")

    @property
    def connection_url(self) -> str:
        if self.DB_TYPE.lower() == "postgresql":
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        self.SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.SQLITE_PATH}"


@dataclass
class SecurityConfig:
    """Security, JWT, & Cryptography Configuration"""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "megacommerce-super-secure-local-jwt-secret-key-2026-v1")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    CORS_ALLOWED_ORIGINS: List[str] = field(default_factory=lambda: [
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ])
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120


@dataclass
class LocalSimulatorsConfig:
    """Local Simulator Operational Settings (Zero API Key Policy)"""
    PAYMENT_GATEWAY_SUCCESS_RATE: float = 0.95
    DELIVERY_SIMULATOR_SPEED_MULTIPLIER: float = 1.0
    DEFAULT_CURRENCY: str = "USD"
    CURRENCY_SYMBOL: str = "$"
    TAX_RATE: float = 0.08  # 8% Tax
    DEFAULT_SHIPPING_FEE: float = 15.00
    FREE_SHIPPING_THRESHOLD: float = 100.00
    INVOICE_STORAGE_DIR: Path = BASE_DIR / "data" / "invoices"

    def __post_init__(self):
        self.INVOICE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class MLServicesConfig:
    """Local Machine Learning & Analytics Engine Settings"""
    RECOMMENDATION_TOP_K: int = 10
    SEARCH_TFIDF_MAX_FEATURES: int = 5000
    SEARCH_FUZZY_THRESHOLD: float = 0.6
    FRAUD_RISK_THRESHOLD_HIGH: float = 0.85
    FRAUD_RISK_THRESHOLD_MEDIUM: float = 0.50
    DEMAND_FORECAST_HORIZON_DAYS: int = 30
    SALES_PREDICTION_LOOKBACK_MONTHS: int = 12
    MODELS_CACHE_DIR: Path = BASE_DIR / "data" / "ml_models"

    def __post_init__(self):
        self.MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    """Root Application Configuration Container"""
    PROJECT_NAME: str = "MegaCommerce Ecosystem"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 5000))
    
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    simulators: LocalSimulatorsConfig = field(default_factory=LocalSimulatorsConfig)
    ml: MLServicesConfig = field(default_factory=MLServicesConfig)


# Global Config Singleton
settings = AppConfig()
