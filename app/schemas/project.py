from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models import ProjectStatus
from app.schemas.place import PlaceCreate, PlaceRead


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    start_date: date | None = None


class ProjectCreate(ProjectBase):
    places: list[PlaceCreate] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_unique_places(self) -> "ProjectCreate":
        external_ids = [place.external_id for place in self.places]
        if len(external_ids) != len(set(external_ids)):
            raise ValueError("Project cannot contain duplicate places")
        return self


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    start_date: date | None = None


class ProjectRead(ProjectBase):
    id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectWithPlacesRead(ProjectRead):
    places: list[PlaceRead]


class ProjectList(BaseModel):
    items: list[ProjectRead]
    total: int
    limit: int
    offset: int
