# MegaCommerce — Complete Full-Stack Commerce Ecosystem

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Zero API Keys](https://img.shields.io/badge/API_Keys-0_Required-success.svg)](#zero-external-api-keys)
[![TrainPlex Benchmark](https://img.shields.io/badge/TrainPlex-PASSED_1.4M_LOC-green.svg)](#trainplex-validation)

MegaCommerce is an enterprise-grade full-stack commerce ecosystem built to operate **100% locally with ZERO external API keys**.

---

## 🌟 Key Features & Core Domains

- **Customer Portal**: Product Browsing, Category Filtering, BM25 TF-IDF Vector Search, Live Autocomplete, Wishlists, Itemized Cart, Instant Checkout Simulation (Card, UPI, Wallet, COD), Order Tracking, and Downloadable ReportLab PDF Sales Invoices.
- **Seller Portal**: Seller Registration & Authentication, Product Management (CRUD with SKUs, Variants & Stock Allocation), Fulfillment Pipeline, and Revenue Analytics.
- **Admin Portal**: Platform Gross Merchandise Value (GMV) Analytics, Fraud Risk Anomaly Monitoring, System Health Dashboard, and Live Security Audit Log Stream.
- **Zero API Key Infrastructure**: Native local algorithms for Search, SVD Recommendations, Naive Bayes Review Sentiment, Holt-Winters Demand Forecasting, and Payment Simulators.

---

## 🛠 Technology Stack

- **Backend**: Python 3.12, Flask 3.0, SQLAlchemy 2.0, PyJWT, Bcrypt, Scikit-Learn, NumPy, ReportLab PDF.
- **Frontend**: Vanilla HTML5, Modern CSS Design System (Glassmorphism, Vibrant Dark Aesthetic), JavaScript Single Page Application (SPA).
- **Database**: SQLite / PostgreSQL (Relational schema with double-entry general ledger, inventory locking, and audit logs).
- **DevOps**: Docker, Docker Compose, GitHub Actions CI pipeline, Pytest, Coverage.

---

## 🚀 Quick Start & Local Execution

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (Optional)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Mallepukusuma26/Megacommerce.git
cd Megacommerce
pip install -r requirements.txt
```

### 2. Initialize Database & Seed Catalog
```bash
python scripts/seed_database.py
```

### 3. Launch Web Application Server
```bash
python app.py
```
Open your browser and navigate to **[http://localhost:5000](http://localhost:5000)**.

---

## 🐳 Docker Deployment

To launch the full production containerized stack:
```bash
docker compose build
docker compose up -d
```
The application will be accessible at `http://localhost:5000`.

---

## 🧪 Testing & Quality Audit

Run the automated Pytest suite (25 unit/integration tests with coverage report):
```bash
python -m pytest tests/
```

Run the TrainPlex Repository Quality Assurer:
```bash
python scripts/validate_project.py
```

---

## 🔒 Security & License

- **Zero External API Keys**: Operating 100% locally with native mathematical solvers and simulators. No third-party API credentials committed or needed.
- **License**: Proprietary / All Rights Reserved.
