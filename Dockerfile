# ==========================================
# Production Dockerfile for AlphaHive
# FastAPI Multi-Agent Engine + React SPA Dist
# ==========================================
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PYTHONPATH=/app/backend

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy Backend Application
COPY backend/ ./backend/

# Copy Pre-compiled Frontend SPA Dist
COPY frontend/dist ./frontend/dist

# Expose Web Port
EXPOSE 8080

# Run Uvicorn Server with dynamic cloud PORT binding
WORKDIR /app/backend
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
