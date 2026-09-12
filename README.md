# MegaCommerce — Complete Full-Stack Commerce Ecosystem

[![Build Status](https://github.com/Mallepukusuma26/Megacommerce/actions/workflows/ci.yml/badge.svg)](https.github.com/Mallepukusuma26/Megacommerce/actions)
![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Zero API Keys](https://img.shields.io/badge/API_Keys-0_Required-success.svg)

MegaCommerce is an enterprise-grade full-stack commerce ecosystem built to operate **100% locally with ZERO external API keys**.

---

## 🌟 Key Features & Core Domains

- **Customer Portal**: Interactive Product Browsing, Category Filtering, TF-IDF Vector Search, Live Search Auto-complete, Wishlists, Itemized Cart, Instant Checkout Simulation, Order Tracking, and Downloadable ReportLab PDF Sales Invoices.
- **Seller Portal**: Seller Registration & Authentication, Product Management (CRUD with SKUs, Variants & Images), Multi-Warehouse Stock Allocation, Order Fulfillment, and Revenue Analytics.
- **Admin Portal**: Platform Gross Revenue Analytics, Moderation Approval Workflows, Fraud Risk Anomaly Monitoring, System Health Dashboard, and Live Audit Log Streaming.
- **Local Service Simulators (Zero API Keys)**:
  - **Payment Simulator**: Card, UPI, Wallet, NetBanking & COD payment gateway simulation.
  - **Delivery Logistics Simulator**: Haversine distance calculations, route optimization, tracking number generation, and delivery agent auto-dispatching.
  - **ReportLab Invoice PDF Generator**: Custom styled PDF invoice generator.
- **Embedded AI / ML Suite**:
  - **Local Search Engine**: Scikit-Learn TF-IDF vectorizer and cosine similarity document matcher with faceted filtering.
  - **Local Recommendation Engine**: Content-based feature similarity, order co-occurrence matrix rules, and top-rated popularity recommendations.
  - **Fraud Detection Module**: Multi-rule velocity checks and anomaly risk scoring.
  - **Time-Series Demand Forecaster**: Ridge regression forecasting product demand 30 days ahead with confidence bounds.
  - **Sales & Revenue Predictor**: 6-month platform revenue forecasting.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.12+
- Git

### Installation & Execution

```bash
# Clone the repository
git clone https://github.com/Mallepukusuma26/Megacommerce.git
cd Megacommerce

# Install dependencies
pip install -r requirements.txt

# Seed initial demo database (Categories, Products, Warehouses, Accounts)
python -m scripts.seed_database

# Run pytest test suite (All 25 tests passing)
python -m pytest tests/

# Launch Application Server
python app.py
```

Access the Web Application UI in your browser at `http://localhost:5000`.

---

## 🐳 Docker Deployment

```bash
# Run using Docker Compose
docker-compose up --build
```

---

## 📊 System Progress Metrics

| Metric | Current Status | Requirement | Status |
|--------|----------------|-------------|--------|
| **External API Keys** | **0** | **0** | 🟢 100% Local |
| **Test Suite Pass Rate** | **25 / 25 Passed** | 100% | 🟢 Complete |
| **Portals Functional** | Customer, Seller & Admin | 3 Portals | 🟢 Complete |
| **Docker & CI Workflows** | Dockerfile, Compose & GitHub Actions | Included | 🟢 Complete |

For detailed technical design and API specifications, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
