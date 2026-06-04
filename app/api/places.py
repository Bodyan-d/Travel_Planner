from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import places as place_crud
from app.crud import projects as project_crud
from app.db.session import get_db
from app.schemas.place import PlaceCreate, PlaceList, PlaceRead, PlaceUpdate
from app.services.artic import ArticClient, get_artic_client

router = APIRouter(prefix="/projects/{project_id}/places", tags=["places"])


def get_project_or_404(project_id: int, db: Session):
    project = project_crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=PlaceRead, status_code=status.HTTP_201_CREATED)
def add_place(
    project_id: int,
    payload: PlaceCreate,
    db: Session = Depends(get_db),
    artic_client: ArticClient = Depends(get_artic_client),
) -> PlaceRead:
    project = get_project_or_404(project_id, db)

    if place_crud.count_project_places(db, project_id) >= place_crud.MAX_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project cannot contain more than 10 places",
        )

    if place_crud.external_place_exists(db, project_id, payload.external_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Place already exists in this project",
        )

    artwork = artic_client.get_artwork(payload.external_id)
    if artwork is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="External place not found in Art Institute API",
        )

    return place_crud.create_place(db, project=project, artwork=artwork, notes=payload.notes)


@router.get("", response_model=PlaceList)
def list_places(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    visited: bool | None = Query(default=None),
) -> PlaceList:
    get_project_or_404(project_id, db)
    items, total = place_crud.list_places(
        db,
        project_id=project_id,
        limit=limit,
        offset=offset,
        visited=visited,
    )
    return PlaceList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{place_id}", response_model=PlaceRead)
def get_place(project_id: int, place_id: int, db: Session = Depends(get_db)) -> PlaceRead:
    get_project_or_404(project_id, db)
    place = place_crud.get_place(db, project_id, place_id)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return place


@router.patch("/{place_id}", response_model=PlaceRead)
def update_place(
    project_id: int,
    place_id: int,
    payload: PlaceUpdate,
    db: Session = Depends(get_db),
) -> PlaceRead:
    project = get_project_or_404(project_id, db)
    place = place_crud.get_place(db, project_id, place_id)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return place_crud.update_place(db, project=project, place=place, payload=payload)
