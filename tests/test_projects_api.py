from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import ProjectPlace, TravelProject
from app.main import app
from app.services.artic import ArticArtwork, get_artic_client


class FakeArticClient:
    def __init__(self, missing_ids: set[str] | None = None) -> None:
        self.missing_ids = missing_ids or set()

    def get_artwork(self, external_id: str) -> ArticArtwork | None:
        if external_id in self.missing_ids:
            return None
        return ArticArtwork(
            external_id=external_id,
            title=f"Artwork {external_id}",
            api_link=f"https://api.artic.edu/api/v1/artworks/{external_id}",
        )


def override_artic_client(client: FakeArticClient) -> None:
    app.dependency_overrides[get_artic_client] = lambda: client


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
    assert data["places"] == []


def test_create_project_with_places(client: TestClient) -> None:
    override_artic_client(FakeArticClient())

    response = client.post(
        "/api/projects",
        json={
            "name": "Chicago art route",
            "places": [
                {"external_id": "123", "notes": "Start here"},
                {"external_id": "456"},
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Chicago art route"
    assert len(data["places"]) == 2
    assert data["places"][0]["external_id"] == "123"
    assert data["places"][0]["notes"] == "Start here"


def test_create_project_with_places_rejects_duplicate_external_ids(client: TestClient) -> None:
    override_artic_client(FakeArticClient())

    response = client.post(
        "/api/projects",
        json={
            "name": "Duplicate route",
            "places": [{"external_id": "123"}, {"external_id": "123"}],
        },
    )

    assert response.status_code == 422


def test_create_project_with_places_rejects_more_than_ten_places(client: TestClient) -> None:
    override_artic_client(FakeArticClient())

    response = client.post(
        "/api/projects",
        json={
            "name": "Too many places",
            "places": [{"external_id": str(index)} for index in range(11)],
        },
    )

    assert response.status_code == 422


def test_create_project_with_places_does_not_persist_when_external_place_is_missing(
    client: TestClient,
) -> None:
    override_artic_client(FakeArticClient(missing_ids={"404"}))

    response = client.post(
        "/api/projects",
        json={
            "name": "Missing artwork route",
            "places": [{"external_id": "123"}, {"external_id": "404"}],
        },
    )
    list_response = client.get("/api/projects")

    assert response.status_code == 404
    assert response.json()["detail"] == "External place 404 not found in Art Institute API"
    assert list_response.json()["total"] == 0


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
