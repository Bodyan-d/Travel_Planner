from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaceCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=64)
    notes: str | None = None


class PlaceUpdate(BaseModel):
    notes: str | None = None
    visited: bool | None = None


class PlaceRead(BaseModel):
    id: int
    project_id: int
    external_id: str
    title: str
    api_link: str | None
    notes: str | None
    visited: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlaceList(BaseModel):
    items: list[PlaceRead]
    total: int
    limit: int
    offset: int
