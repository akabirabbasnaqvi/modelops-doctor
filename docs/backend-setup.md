# ModelOps Doctor Backend Setup

## Requirements

- Python 3.11
- PostgreSQL 16
- Docker Desktop
- Git

## Create the Virtual Environment

From the project root:

```powershell
py -3.11 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
```

## Install Dependencies

```powershell
python -m pip install -r backend\requirements.txt
```

## Configure Environment Variables

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Update the PostgreSQL password and other local configuration in `.env`.

Never commit `.env` to Git.

## Run Database Migrations

```powershell
cd backend
python -m alembic upgrade head
```

## Run FastAPI

From the `backend` directory:

```powershell
python -m uvicorn app.main:app --reload
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/api/v1/health
```

## Run Redis Locally

Create the Redis container once:

```powershell
docker run -d --name modelops-redis -p 6379:6379 redis:7-alpine
```

If the container already exists, start it:

```powershell
docker start modelops-redis
```

Test Redis:

```powershell
docker exec modelops-redis redis-cli ping
```

Expected response:

```text
PONG
```

## Run Celery Worker on Windows

From the `backend` directory:

```powershell
python -m celery -A app.workers.celery_app:celery_app worker --loglevel=info --pool=solo
```

## Run Celery Beat

From the `backend` directory:

```powershell
python -m celery -A app.workers.celery_app:celery_app beat --loglevel=info
```

## Run Tests

```powershell
cd backend
python -m pytest
```

## Run Ruff

```powershell
cd backend
python -m ruff check app tests alembic\env.py
python -m ruff format --check app tests alembic\env.py
```

## Run with Docker Compose

From the project root:

```powershell
docker compose up --build
```

Swagger documentation:

```text
http://localhost:8000/docs
```

Stop the services:

```powershell
docker compose down
```

Reset container data only when necessary:

```powershell
docker compose down -v
```

The `-v` option permanently deletes the Docker PostgreSQL and Redis volumes.