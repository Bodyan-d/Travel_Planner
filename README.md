# Travel Planner API

FastAPI CRUD application for managing travel projects, project places imported from the Art Institute of Chicago API, and traveller notes.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Docker

```powershell
docker compose up --build
```

The Docker setup stores the SQLite database in a named volume and exposes the API on `http://127.0.0.1:8000`.

## Postman

Import `postman/Travel_Planner.postman_collection.json` into Postman. The collection uses `base_url`, `username`, and `password` variables with local defaults.

## Current status

Implemented project and project-place CRUD endpoints with Art Institute of Chicago API validation.

Art Institute API responses are cached in memory for 300 seconds by default. Override with `ARTIC_CACHE_TTL_SECONDS`.

Management endpoints require HTTP Basic authentication. Defaults are `admin` / `admin`; override with `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD`.
