# MegaCommerce Master System Architecture & Technical Manual

## Executive Summary
MegaCommerce is an enterprise-grade full-stack commerce ecosystem featuring Customer, Seller, and Admin Portals, an embedded AI/ML suite, Local Service Simulators (Payment Gateway, Logistics Delivery Dispatcher, ReportLab PDF Invoices), Comprehensive Analytics, and Multi-Warehouse Inventory Allocation.

The platform operates **100% locally with ZERO external API keys**, utilizing native Python algorithms, scikit-learn, numpy, pandas, xgboost, and SQLAlchemy ORM.

---

## 1. High-Level System Architecture

```
                                  +---------------------------------------+
                                  |        Web SPA Frontend (HTML5)       |
                                  |   Customer, Seller & Admin Portals    |
                                  +------------------+--------------------+
                                                     |
                                                     v (JSON REST APIs)
+----------------------------------------------------+----------------------------------------------------+
|                                     MegaCommerce Application Server (Flask)                              |
|                                                                                                         |
|  +--------------------+  +--------------------+  +--------------------+  +----------------------------+ |
|  |    Auth & RBAC     |  |   Catalog Engine   |  |   Cart & Orders    |  |    Inventory & Warehouse   | |
|  +--------------------+  +--------------------+  +--------------------+  +----------------------------+ |
|                                                                                                         |
|  +---------------------------------------------------------------------------------------------------+  |
|  |                                  Local Simulators (Zero API Keys)                                 |  |
|  |  [ Payment Simulator ]        [ Delivery Logistics Dispatcher ]       [ ReportLab PDF Invoicing ] |  |
|  +---------------------------------------------------------------------------------------------------+  |
|                                                                                                         |
|  +---------------------------------------------------------------------------------------------------+  |
|  |                                     Local AI / ML Engine Suite                                    |  |
|  |  [ TF-IDF Vector Search ]  [ Content & Collaborative AI Recs ]  [ Anomaly Fraud ]  [ Forecasting ]  |  |
|  +---------------------------------------------------------------------------------------------------+  |
+----------------------------------------------------+----------------------------------------------------+
                                                     |
                                                     v (SQLAlchemy ORM)
                                  +------------------+--------------------+
                                  |    Normalized SQLite / PostgreSQL     |
                                  +---------------------------------------+
```

---

## 2. Zero External API Key Compliance Matrix

| Real-World Cloud Service | MegaCommerce Local Simulator | Algorithm / Implementation |
|--------------------------|------------------------------|----------------------------|
| **OpenAI / Gemini API** | Embedded Python ML Models | Scikit-learn TF-IDF, Cosine Similarity, Ridge & SVD |
| **Stripe / Razorpay API** | `PaymentSimulatorEngine` | Local Card, UPI, Wallet, NetBanking & COD lifecycle |
| **Google Maps / Shipping API**| `DeliverySimulatorEngine` | Local Haversine Distance & Agent Dispatcher |
| **Cloud Search (Algolia)** | `LocalSearchEngine` | In-Memory TF-IDF & N-Gram Cosine Vector Indexer |
| **Cloud Fraud (Sift/Signifyd)**| `LocalFraudDetector` | Velocity checks, anomaly scoring & risk rules |

---

## 3. Database Schema Entity Relationships

- **Users (`users`)**: Stores Customer, Seller, Admin, Audit, and Delivery Agent identities with bcrypt hashed passwords.
- **Addresses (`addresses`)**: Delivery & Billing locations with default flags.
- **Seller Profiles (`seller_profiles`)**: Stores seller store details, sales count, ratings, and total revenue.
- **Products & Variants (`products`, `product_variants`, `product_images`)**: Catalog items with SKUs, pricing, discount pricing, stock, attributes, and image galleries.
- **Warehouses & Inventories (`warehouses`, `inventory_items`, `stock_reservations`)**: Multi-facility stock allocation, bin locations, and order reservation tracking.
- **Carts & Wishlists (`carts`, `cart_items`, `wishlists`, `wishlist_items`)**: Shopping cart state and promotional coupon links.
- **Orders & Payments (`orders`, `order_items`, `payment_transactions`, `order_histories`)**: Complete order lifecycle from `CREATED` to `DELIVERED` / `REFUNDED`.
- **Logistics & Returns (`shipments`, `shipment_events`, `return_requests`, `refund_transactions`)**: Delivery tracking numbers, transit events, return inspection, and credit refunds.

---

## 4. REST API Endpoint Catalog

### Authentication & Profiles (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Customer or Seller account creation.
- `POST /api/v1/auth/login`: Authenticate and issue Bearer JWT access token.
- `GET /api/v1/auth/me`: Retrieve current authenticated profile.
- `POST /api/v1/auth/addresses`: Add new billing/shipping address.

### Product Catalog (`/api/v1/catalog`)
- `GET /api/v1/catalog/categories`: List active categories.
- `POST /api/v1/catalog/categories`: Create category (Admin only).
- `GET /api/v1/catalog/brands`: List active brands.
- `POST /api/v1/catalog/products`: Seller creates product listing.
- `GET /api/v1/catalog/products`: Filter products by category, brand, price range, and rating.
- `GET /api/v1/catalog/products/<id_or_slug>`: Detail view with variants.

### Cart & Checkout (`/api/v1/cart`, `/api/v1/orders`)
- `GET /api/v1/cart`: Itemized cart breakdown with tax & shipping math.
- `POST /api/v1/cart/items`: Add product item to cart.
- `PUT /api/v1/cart/items/<id>`: Update item quantity.
- `DELETE /api/v1/cart/items/<id>`: Remove item.
- `POST /api/v1/cart/coupon`: Apply promotional coupon code.
- `POST /api/v1/orders/checkout`: Place order, reserve stock, and simulate payment.
- `GET /api/v1/orders/history`: Retrieve customer order history.

### Local Search & ML Recommendations (`/api/v1/search`, `/api/v1/recommendations`)
- `POST /api/v1/search/query`: TF-IDF full-text vector query matching.
- `GET /api/v1/search/suggestions`: Auto-complete search prefix suggestions.
- `GET /api/v1/recommendations/similar/<product_id>`: Content-based recommendations.
- `GET /api/v1/recommendations/popular`: Top-rated product recommendations.

### Advanced Services & Analytics (`/api/v1`)
- `GET /api/v1/invoices/<order_id>/pdf`: Download generated ReportLab PDF sales invoice.
- `POST /api/v1/returns/request`: Submit customer return request.
- `GET /api/v1/fraud/assess/<order_id>`: Evaluate order fraud risk score (Admin).
- `GET /api/v1/analytics/forecast/demand/<product_id>`: 30-day time-series demand forecast.
- `GET /api/v1/analytics/predictions/sales`: 6-month revenue trend prediction.
- `GET /api/v1/analytics/customer`: Customer spending segment analytics.
- `GET /api/v1/analytics/seller`: Seller revenue & turnover metrics.
- `GET /api/v1/analytics/admin`: Platform gross revenue & audit log stream.

---

## 5. Running the Application Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed initial demo data
python -m scripts.seed_database

# 3. Run full test suite
python -m pytest tests/

# 4. Start Application Server
python app.py
```
Open `http://localhost:5000` in your web browser.
