from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ProjectPlace, ProjectStatus, TravelProject
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, payload: ProjectCreate) -> TravelProject:
    project = TravelProject(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(
    db: Session,
    *,
    limit: int,
    offset: int,
    status: ProjectStatus | None = None,
    search: str | None = None,
) -> tuple[list[TravelProject], int]:
    statement = select(TravelProject)
    count_statement = select(func.count()).select_from(TravelProject)

    filters = []
    if status is not None:
        filters.append(TravelProject.status == status)
    if search:
        filters.append(TravelProject.name.ilike(f"%{search}%"))

    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)

    total = db.scalar(count_statement) or 0
    projects = list(
        db.scalars(
            statement.order_by(TravelProject.created_at.desc(), TravelProject.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return projects, total


def get_project(db: Session, project_id: int) -> TravelProject | None:
    return db.get(TravelProject, project_id)


def update_project(db: Session, project: TravelProject, payload: ProjectUpdate) -> TravelProject:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(project, field, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def project_has_visited_places(db: Session, project_id: int) -> bool:
    statement = select(ProjectPlace.id).where(
        ProjectPlace.project_id == project_id,
        ProjectPlace.visited.is_(True),
    )
    return db.scalar(statement) is not None


def delete_project(db: Session, project: TravelProject) -> None:
    db.delete(project)
    db.commit()
