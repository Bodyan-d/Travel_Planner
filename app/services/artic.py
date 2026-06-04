from dataclasses import dataclass

import httpx
from fastapi import Depends

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class ArticArtwork:
    external_id: str
    title: str
    api_link: str | None


class ArticClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def get_artwork(self, external_id: str) -> ArticArtwork | None:
        url = f"{self.base_url}/artworks/{external_id}"
        try:
            response = httpx.get(
                url,
                params={"fields": "id,title,api_link"},
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise

        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, dict) or data.get("id") is None:
            return None

        return ArticArtwork(
            external_id=str(data["id"]),
            title=data.get("title") or f"Artwork {external_id}",
            api_link=data.get("api_link"),
        )


def get_artic_client(settings: Settings = Depends(get_settings)) -> ArticClient:
    return ArticClient(settings.artic_base_url)
