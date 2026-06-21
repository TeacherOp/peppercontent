# Atlas Report Builder — production image (gunicorn).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persisted report store — mount a Coolify volume here so saved reports
# survive redeploys/restarts.
RUN mkdir -p /app/data/reports
VOLUME ["/app/data"]

EXPOSE 8000

# Claude calls take several seconds, so give workers a generous timeout.
# Keep a single worker (with threads) so the file-based JSON store has one writer.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "120", "app:app"]
