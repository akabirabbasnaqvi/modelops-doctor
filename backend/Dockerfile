FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.lock.txt /app/backend/requirements.lock.txt

# Install from the lockfile so every image build resolves to the same
# transitive versions.
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/backend/requirements.lock.txt

COPY backend /app/backend
COPY ml_examples /app/ml_examples

RUN mkdir -p /app/storage \
    && chmod +x /app/backend/docker-entrypoint.sh

WORKDIR /app/backend

EXPOSE 8000

ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]