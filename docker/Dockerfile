# ================================================================
# MEGACOMMERCE — PRODUCTION DOCKER CONTAINER
# Zero External API Key Architecture
# ================================================================

FROM python:3.12-slim as base

# Set working directory
WORKDIR /app

# Prevent Python from writing bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Initialize data directories
RUN mkdir -p data/invoices data/ml_models

# Expose server port
EXPOSE 5000

# Run Application Server
CMD ["python", "app.py"]
