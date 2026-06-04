from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import ProjectPlace, TravelProject


def test_create_project(client: TestClient) -> None:
    response = client.post(
        "/api/projects",
        json={"name": "Paris museums", "description": "Spring trip", "start_date": "2026-04-10"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Paris museums"
    assert data["status"] == "active"


def test_list_projects_supports_pagination_and_search(client: TestClient) -> None:
    client.post("/api/projects", json={"name": "Kyoto"})
    client.post("/api/projects", json={"name": "Paris"})

    response = client.get("/api/projects", params={"limit": 1, "offset": 0, "search": "Par"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert data["items"][0]["name"] == "Paris"


def test_get_project_returns_404_for_missing_project(client: TestClient) -> None:
    response = client.get("/api/projects/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_update_project(client: TestClient) -> None:
    created = client.post("/api/projects", json={"name": "Old name"}).json()

    response = client.patch(
        f"/api/projects/{created['id']}",
        json={"name": "New name", "description": "Updated"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New name"
    assert data["description"] == "Updated"


def test_delete_project(client: TestClient) -> None:
    created = client.post("/api/projects", json={"name": "Temporary"}).json()

    response = client.delete(f"/api/projects/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/projects/{created['id']}").status_code == 404


def test_delete_project_with_visited_places_is_blocked(
    client: TestClient,
    db_session: Session,
) -> None:
    project = TravelProject(name="Visited project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    db_session.add(
        ProjectPlace(
            project_id=project.id,
            external_id="123",
            title="Visited artwork",
            visited=True,
        )
    )
    db_session.commit()

    response = client.delete(f"/api/projects/{project.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Project cannot be deleted because it has visited places"
