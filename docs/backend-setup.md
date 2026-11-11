# ModelOps Doctor Backend Setup

## Requirements

- Python 3.11
- PostgreSQL 16
- Docker Desktop
- Git

## Create the Virtual Environment

From the project root.

Linux and macOS:

```bash
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate
```

Windows (PowerShell):

```powershell
py -3.11 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
```

## Install Dependencies

Linux and macOS:

```bash
python -m pip install -r backend/requirements-dev.txt
```

Windows (PowerShell):

```powershell
python -m pip install -r backend\requirements-dev.txt
```

`requirements.txt` holds the runtime dependencies. `requirements-dev.txt`
adds pytest, pytest-cov, httpx, Ruff, and pip-audit, and is what CI installs.
It constrains runtime versions to `requirements.lock.txt`, matching Docker.

## Configure Environment Variables

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

The example uses the local Compose PostgreSQL and Redis ports (5433 and
6380) and demo credentials. If you use your own services, update `.env`
to match them. Existing `.env` files are not changed by setup.

Never commit `.env` to Git.

## Start PostgreSQL and Redis

From the repository root, before running migrations:

```powershell
docker compose up -d --wait db redis
docker compose exec redis redis-cli ping
```

The Redis check returns `PONG`. Keep these containers running while using
the local API, worker, and Beat.

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

Redis was started with PostgreSQL above. From the repository root, check it:

```powershell
docker compose exec redis redis-cli ping
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

Tests use fake repositories and temporary files; PostgreSQL and Redis do
not need to be running for the current unit/API health suite.

```powershell
cd backend
python -m pytest
```

## Audit Runtime Dependencies

From `backend/`, run the same gate as CI:

```powershell
python -m pip_audit --strict --no-deps --disable-pip --requirement requirements.lock.txt
```

The lock is fully pinned, so pip-audit can check every listed package
without trying to install Linux-only packages on Windows.

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
