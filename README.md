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

## Current status

Initial FastAPI project skeleton with a health endpoint.
