# AI CV Screening Backend

This project is a Django-based backend service that automates the initial screening of job applications. It uses a RAG (Retrieval-Augmented Generation) pipeline to evaluate a candidate's CV and project report against a job description and a case study brief.

## Features

-   **RESTful API**: Endpoints for uploading documents, triggering evaluations, and retrieving results.
-   **Asynchronous Processing**: Uses Celery and Redis to handle long-running AI evaluation tasks without blocking API requests.
-   **RAG Pipeline**: Ingests reference documents into a ChromaDB vector store and retrieves them to provide context to an LLM for evaluation.
-   **LLM Chaining**: Uses Langchain to structure the evaluation process into multiple steps (CV evaluation, project report evaluation, final summary).
-   **Secure Endpoints**: API endpoints are protected using JWT authentication.

## Project Structure

-   `cv_screening`: The main Django project directory.
-   `api`: A Django app for the RESTful API (views, serializers, URLs).
-   `evaluations`: A Django app for the data models, Celery tasks, and AI pipeline logic.
-   `documents`: Contains the internal documents used for the RAG system and the ingestion script.
-   `chroma_db`: The directory where the ChromaDB vector store is persisted.
-   `media`: The directory where uploaded CVs and project reports are stored.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd cv-screening
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

*** Begin README replacement
# AI CV Screening — Detailed README

This repository contains a Django-based backend service that automates screening of candidate CVs and project reports using a Retrieval-Augmented Generation (RAG) pipeline and an LLM. The system accepts uploaded documents, builds/queries a vector store for context, and runs asynchronous evaluation jobs via Celery.

## Contents of this README
- Project summary
- Architecture and components
- Quickstart (development)
- Configuration and environment variables
- How to run (dev & production notes)
- API endpoints and examples
- Security & hardening measures applied
- Testing and load testing
- Deployment notes (Nginx, Gunicorn, Celery)
- Troubleshooting and helpful commands
- How to contribute

## Project summary

- Purpose: assist with initial candidate screening by scoring CVs and project reports against job descriptions and evaluation rubrics.
- Main capabilities: file upload, asynchronous evaluation (Celery), vector search (Chroma), LLM-based scoring (Langchain + Google LLM), REST API (DRF).

## Architecture & components

- Django project: `cv_screening/`
- Apps:
  - `api/` — REST endpoints, serializers, auth
  - `evaluations/` — models for evaluation jobs, Celery tasks, views for results
  - `core/` — domain/use-case logic (clean architecture: use cases, interfaces, infra)
- Async queue: Celery workers; broker & result backend: Redis (configurable)
- Vector store: Chroma (used via `core/infra/vector_store/chroma.py`)
- LLM service: Google Gemini integration in `core/infra/llm/google.py`
- Storage: uploaded files in `media/` (configured in `settings.py`)

## Quickstart — development (Windows / PowerShell)

1. Clone the repository and open a PowerShell terminal:

```powershell
git clone <repository-url>
cd cv-screening-master
```

2. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Copy example env and edit values:

```powershell
copy .env.example .env
# Edit .env with a text editor and add secrets (SECRET_KEY, GOOGLE_API_KEY, etc.)
```

5. Apply migrations and create a superuser:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

6. (Optional) Ingest reference documents used by RAG:

```powershell
python manage.py ingest
```

7. Start required services (in separate terminals):

- Redis (must be installed separately) — ensure `redis-server` is running.
- Celery worker:

```powershell
celery -A cv_screening worker --loglevel=info
```

- Django dev server:

```powershell
python manage.py runserver
```

You can now interact with the API at http://localhost:8000

## Configuration & environment variables

- Use the `.env` file (template: `.env.example`) — do not commit secrets.
- Important variables:
  - `SECRET_KEY` — Django secret key
  - `DEBUG` — False in production
  - `ALLOWED_HOSTS` — hostnames for production
  - `DATABASE_URL` — DB connection (SQLite default; use PostgreSQL in production)
  - `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`
  - `GOOGLE_API_KEY` — LLM provider key
  - `FILE_UPLOAD_MAX_MEMORY_SIZE` / `DATA_UPLOAD_MAX_MEMORY_SIZE`

Settings to review in `cv_screening/settings.py` include DRF authentication (SimpleJWT), upload limits, throttling rates, and security flags.

## API endpoints (overview)

All API endpoints require authentication (JWT) unless noted otherwise.

- `POST /api/upload/` — Upload a file (CV/project report). Returns uploaded file metadata including `id`.
  - Throttle: 5 requests/minute (per user/IP)
  - Valid file types: PDF, DOC, DOCX
  - Max file size: 2 MB (configurable)

- `POST /api/evaluate/` — Trigger an evaluation job. Body: `{ job_title, cv_id, project_report_id }`.
  - Creates an `EvaluationJob` record and enqueues a Celery task.
  - Throttle: 2 requests/minute (per user/IP)

- `GET /api/result/<job_id>/` — Retrieve job status and results.

- Auth endpoints (JWT): `/api/token/`, `/api/token/refresh/` (provided by SimpleJWT)

Refer to `api/views.py` and `api/serializers.py` for exact request/response shapes.

## Security & hardening (what's implemented)

These are the production-minded measures already added to the codebase:

- Application-level rate limiting using DRF throttles (scopes: `upload_cv`, `start_evaluation`, global anon/user limits).
- Edge/proxy example config (`nginx-config.example`) with `limit_req_zone` and `limit_conn` rules.
- File upload checks in `api/serializers.py` (size and content-type restrictions).
- Login brute-force protection with `django-axes` (lockout after failed attempts).
- Enforced TLS-related settings in `settings.py`: `SECURE_SSL_REDIRECT`, HSTS, secure cookies, `X-Frame-Options`, content-type nosniff, XSS protection.
- Celery task-level rate/time limits (`@shared_task(rate_limit='5/m', time_limit=300)`).
- Secrets isolated to `.env` (recommend secret manager for production).

Further recommendations (see `SECURITY_HARDENING.md`): virus scanning (ClamAV), WAF, Sentry/Prometheus monitoring, broker TLS and network isolation, and DB backups.

## Tests & load testing

- Unit tests are in `api/tests.py` (throttle & file validation tests included).

Run tests:

```powershell
python manage.py test
```

Load testing with Locust (example included as `locustfile.py`):

```powershell
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

Open Locust UI at http://localhost:8089 to run scenarios (includes burst users for throttle testing).

## Deployment notes

Recommended production stack:

- Gunicorn as WSGI server (or Daphne/Uvicorn for ASGI if using async features)
- Nginx as reverse proxy and TLS terminator (see `nginx-config.example`)
- PostgreSQL database
- Redis (or RabbitMQ) for Celery broker/result backend — secured and not exposed publicly
- Systemd service or process supervisor for Gunicorn and Celery workers
- Logging and monitoring (Sentry for errors, Prometheus/Grafana for metrics)

Sample Gunicorn systemd service and Celery systemd snippets are included in `DEPLOYMENT.md`.

## Troubleshooting & common commands

- Run migrations:

```powershell
python manage.py migrate
```

- Run tests with verbosity:

```powershell
python manage.py test -v 2
```

- Start a single Celery worker (in project root):

```powershell
celery -A cv_screening worker --loglevel=info
```

- If you hit `429 Too Many Requests`, check throttle settings in `cv_screening/settings.py` and the Nginx config for edge limits.

## Code structure and where to look

- `api/views.py` — endpoints for upload/evaluate/result
- `api/serializers.py` — validation and serialization rules (file validation)
- `evaluations/tasks.py` — Celery tasks that compose the evaluation use-case
- `core/application/use_cases/evaluate_candidate.py` — business logic use-case
- `core/infra/llm/google.py` — LLM integration
- `core/infra/vector_store/chroma.py` — vector store adapter

## Contributing

- Fork, create a feature branch, run tests, open a pull request.
- Add unit tests for any new behavior and keep changes small and reviewable.

If you'd like, I can:
- produce an OpenAPI/Swagger spec for the API,
- add CI (GitHub Actions) to run lint/tests, or
- prepare a production-ready `docker-compose` and `Dockerfile` set for containerized deploys.

Thank you — if you want this README tuned (shorter, more diagrams, or include ER diagrams / sequence diagrams), tell me which sections to expand and I'll update it.

*** End README replacement
