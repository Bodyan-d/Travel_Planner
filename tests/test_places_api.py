from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import ProjectPlace, ProjectStatus, TravelProject
from app.services.artic import ArticArtwork, get_artic_client
from app.main import app


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


def create_project(client: TestClient, name: str = "Art trip") -> dict:
    response = client.post("/api/projects", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_add_place_validates_external_artwork(client: TestClient) -> None:
    override_artic_client(FakeArticClient())
    project = create_project(client)

    response = client.post(
        f"/api/projects/{project['id']}/places",
        json={"external_id": "123", "notes": "Main stop"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["external_id"] == "123"
    assert data["title"] == "Artwork 123"
    assert data["notes"] == "Main stop"
    assert data["visited"] is False


def test_add_place_returns_404_when_external_artwork_is_missing(client: TestClient) -> None:
    override_artic_client(FakeArticClient(missing_ids={"404"}))
    project = create_project(client)

    response = client.post(
        f"/api/projects/{project['id']}/places",
        json={"external_id": "404"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "External place not found in Art Institute API"


def test_add_place_prevents_duplicates(client: TestClient) -> None:
    override_artic_client(FakeArticClient())
    project = create_project(client)
    url = f"/api/projects/{project['id']}/places"
    assert client.post(url, json={"external_id": "123"}).status_code == 201

    response = client.post(url, json={"external_id": "123"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Place already exists in this project"


def test_add_place_enforces_maximum_places(
    client: TestClient,
    db_session: Session,
) -> None:
    override_artic_client(FakeArticClient())
    project = TravelProject(name="Full project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    for index in range(10):
        db_session.add(
            ProjectPlace(
                project_id=project.id,
                external_id=str(index),
                title=f"Artwork {index}",
            )
        )
    db_session.commit()

    response = client.post(
        f"/api/projects/{project.id}/places",
        json={"external_id": "11"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Project cannot contain more than 10 places"


def test_list_and_get_places(client: TestClient) -> None:
    override_artic_client(FakeArticClient())
    project = create_project(client)
    created = client.post(
        f"/api/projects/{project['id']}/places",
        json={"external_id": "123"},
    ).json()

    list_response = client.get(f"/api/projects/{project['id']}/places")
    get_response = client.get(f"/api/projects/{project['id']}/places/{created['id']}")

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_update_place_notes_and_mark_visited_completes_project(client: TestClient) -> None:
    override_artic_client(FakeArticClient())
    project = create_project(client)
    place = client.post(
        f"/api/projects/{project['id']}/places",
        json={"external_id": "123"},
    ).json()

    response = client.patch(
        f"/api/projects/{project['id']}/places/{place['id']}",
        json={"notes": "Visited on day two", "visited": True},
    )
    project_response = client.get(f"/api/projects/{project['id']}")

    assert response.status_code == 200
    assert response.json()["notes"] == "Visited on day two"
    assert response.json()["visited"] is True
    assert project_response.json()["status"] == ProjectStatus.COMPLETED
