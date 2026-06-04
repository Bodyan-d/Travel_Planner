from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ProjectPlace, ProjectStatus, TravelProject
from app.schemas.place import PlaceUpdate
from app.services.artic import ArticArtwork

MAX_PLACES_PER_PROJECT = 10


def count_project_places(db: Session, project_id: int) -> int:
    statement = select(func.count()).select_from(ProjectPlace).where(ProjectPlace.project_id == project_id)
    return db.scalar(statement) or 0


def external_place_exists(db: Session, project_id: int, external_id: str) -> bool:
    statement = select(ProjectPlace.id).where(
        ProjectPlace.project_id == project_id,
        ProjectPlace.external_id == external_id,
    )
    return db.scalar(statement) is not None


def create_place(
    db: Session,
    *,
    project: TravelProject,
    artwork: ArticArtwork,
    notes: str | None,
) -> ProjectPlace:
    place = ProjectPlace(
        project_id=project.id,
        external_id=artwork.external_id,
        title=artwork.title,
        api_link=artwork.api_link,
        notes=notes,
    )
    db.add(place)
    project.status = ProjectStatus.ACTIVE
    db.commit()
    db.refresh(place)
    return place


def list_places(
    db: Session,
    *,
    project_id: int,
    limit: int,
    offset: int,
    visited: bool | None = None,
) -> tuple[list[ProjectPlace], int]:
    statement = select(ProjectPlace).where(ProjectPlace.project_id == project_id)
    count_statement = select(func.count()).select_from(ProjectPlace).where(ProjectPlace.project_id == project_id)

    if visited is not None:
        statement = statement.where(ProjectPlace.visited.is_(visited))
        count_statement = count_statement.where(ProjectPlace.visited.is_(visited))

    total = db.scalar(count_statement) or 0
    places = list(
        db.scalars(
            statement.order_by(ProjectPlace.created_at.desc(), ProjectPlace.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return places, total


def get_place(db: Session, project_id: int, place_id: int) -> ProjectPlace | None:
    statement = select(ProjectPlace).where(
        ProjectPlace.project_id == project_id,
        ProjectPlace.id == place_id,
    )
    return db.scalar(statement)


def update_place(
    db: Session,
    *,
    project: TravelProject,
    place: ProjectPlace,
    payload: PlaceUpdate,
) -> ProjectPlace:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(place, field, value)

    db.add(place)
    db.flush()
    sync_project_completion(db, project)
    db.commit()
    db.refresh(place)
    return place


def sync_project_completion(db: Session, project: TravelProject) -> None:
    total_places = count_project_places(db, project.id)
    if total_places == 0:
        project.status = ProjectStatus.ACTIVE
        return

    unvisited_statement = select(ProjectPlace.id).where(
        ProjectPlace.project_id == project.id,
        ProjectPlace.visited.is_(False),
    )
    project.status = (
        ProjectStatus.ACTIVE if db.scalar(unvisited_statement) is not None else ProjectStatus.COMPLETED
    )
