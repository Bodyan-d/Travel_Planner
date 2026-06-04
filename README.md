# Travel Planner API

FastAPI CRUD application for managing travel projects, project places imported from the Art Institute of Chicago API, and traveller notes.

## Features

- Create, list, retrieve, update, and delete travel projects.
- Create a project with imported places in one request.
- Add Art Institute artworks as project places after validating them through the public API.
- List, retrieve, and update project places.
- Store and update traveller notes for each place.
- Mark places as visited.
- Automatically mark a project as completed when all of its places are visited.
- Prevent deleting a project that has visited places.
- Enforce a maximum of 10 places per project.
- Prevent duplicate external places inside the same project.
- Pagination and filtering for list endpoints.
- In-memory TTL cache for Art Institute API responses.
- HTTP Basic authentication for management endpoints.
- Docker and Postman support.

## Tech Stack

- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- HTTPX
- Pytest

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

API docs are available at `http://127.0.0.1:8000/docs`.

## Docker

```powershell
docker compose up --build
```

The Docker setup stores the SQLite database in a named volume and exposes the API on `http://127.0.0.1:8000`.

## Authentication

Management endpoints require HTTP Basic authentication.

Default credentials:

```text
username: admin
password: admin
```

The health endpoint is public:

```text
GET /api/health
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./travel_planner.db` | SQLAlchemy database URL. |
| `ARTIC_BASE_URL` | `https://api.artic.edu/api/v1` | Art Institute of Chicago API base URL. |
| `ARTIC_CACHE_TTL_SECONDS` | `300` | TTL for cached Art Institute API responses. Use `0` to disable caching. |
| `BASIC_AUTH_USERNAME` | `admin` | HTTP Basic username. |
| `BASIC_AUTH_PASSWORD` | `admin` | HTTP Basic password. |

## Endpoints

### Health

```text
GET /api/health
```

### Projects

```text
POST   /api/projects
GET    /api/projects
GET    /api/projects/{project_id}
PATCH  /api/projects/{project_id}
DELETE /api/projects/{project_id}
```

`GET /api/projects` supports:

```text
limit
offset
status
search
```

Example project creation with places:

```json
{
  "name": "Chicago Art Trip",
  "description": "Weekend route",
  "start_date": "2026-07-01",
  "places": [
    {
      "external_id": "129884",
      "notes": "First stop"
    }
  ]
}
```

### Project Places

```text
POST  /api/projects/{project_id}/places
GET   /api/projects/{project_id}/places
GET   /api/projects/{project_id}/places/{place_id}
PATCH /api/projects/{project_id}/places/{place_id}
```

`GET /api/projects/{project_id}/places` supports:

```text
limit
offset
visited
```

Example place creation:

```json
{
  "external_id": "129884",
  "notes": "Imported from Art Institute API"
}
```

Example place update:

```json
{
  "notes": "Visited on day two",
  "visited": true
}
```

## Postman

Import `postman/Travel_Planner.postman_collection.json` into Postman.

The collection uses these variables with local defaults:

```text
base_url = http://127.0.0.1:8000/api
username = admin
password = admin
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The test suite covers project CRUD, place CRUD, authentication, Art Institute API caching, validation rules, and project completion behavior.
