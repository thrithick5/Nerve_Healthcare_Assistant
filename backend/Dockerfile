FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

# Migrations are best-effort: an unreachable database must not stop the API
# from booting (pool_pre_ping reconnects once the database is reachable).
CMD ["sh", "-c", "python scripts/run_migrations.py; exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
