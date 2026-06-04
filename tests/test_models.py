from datetime import date

from app.db.models import ProjectPlace, ProjectStatus, TravelProject


def test_project_model_defaults() -> None:
    project = TravelProject(name="Rome", start_date=date(2026, 7, 1))

    assert project.name == "Rome"
    assert project.start_date == date(2026, 7, 1)
    assert project.status is None


def test_project_place_unique_identity_fields() -> None:
    place = ProjectPlace(external_id="123", title="Artwork title")

    assert place.external_id == "123"
    assert place.title == "Artwork title"
    assert place.visited is None
