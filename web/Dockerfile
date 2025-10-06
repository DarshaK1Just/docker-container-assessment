# Use official Python slim image
FROM python:3.11-slim AS builder


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


# Install system deps needed for some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


# Copy and install dependencies first (caching)
COPY web/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt


# Copy application code
COPY web /app


# Create a non-root user for security
RUN useradd --create-home appuser || true
RUN chown -R appuser:appuser /app
USER appuser


EXPOSE 5000


# Use Gunicorn for production
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]