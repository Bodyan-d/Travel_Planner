from fastapi.testclient import TestClient

from tests.conftest import basic_auth_header


def test_health_endpoint_does_not_require_auth(unauthenticated_client: TestClient) -> None:
    response = unauthenticated_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_project_endpoints_require_auth(unauthenticated_client: TestClient) -> None:
    response = unauthenticated_client.get("/api/projects")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Basic"


def test_project_endpoints_reject_invalid_auth(unauthenticated_client: TestClient) -> None:
    response = unauthenticated_client.get(
        "/api/projects",
        headers=basic_auth_header(username="admin", password="wrong"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication credentials"


def test_project_endpoints_accept_valid_auth(unauthenticated_client: TestClient) -> None:
    response = unauthenticated_client.get("/api/projects", headers=basic_auth_header())

    assert response.status_code == 200
