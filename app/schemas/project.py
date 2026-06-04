from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ProjectStatus


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    start_date: date | None = None


class ProjectCreate(ProjectBase):
    pass


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


class ProjectList(BaseModel):
    items: list[ProjectRead]
    total: int
    limit: int
    offset: int
