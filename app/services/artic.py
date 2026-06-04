from dataclasses import dataclass
from time import monotonic

import httpx
from fastapi import Depends

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class ArticArtwork:
    external_id: str
    title: str
    api_link: str | None


@dataclass(frozen=True)
class CachedArtwork:
    value: ArticArtwork | None
    expires_at: float


class ArticClient:
    def __init__(
        self,
        base_url: str,
        *,
        cache_ttl_seconds: int,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_ttl_seconds = cache_ttl_seconds
        self.http_client = http_client or httpx.Client(timeout=10)
        self._cache: dict[str, CachedArtwork] = {}

    def get_artwork(self, external_id: str) -> ArticArtwork | None:
        cached = self._cache.get(external_id)
        now = monotonic()
        if cached is not None and cached.expires_at > now:
            return cached.value

        url = f"{self.base_url}/artworks/{external_id}"
        try:
            response = self.http_client.get(
                url,
                params={"fields": "id,title,api_link"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                self._remember(external_id, None)
                return None
            raise

        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, dict) or data.get("id") is None:
            self._remember(external_id, None)
            return None

        artwork = ArticArtwork(
            external_id=str(data["id"]),
            title=data.get("title") or f"Artwork {external_id}",
            api_link=data.get("api_link"),
        )
        self._remember(external_id, artwork)
        return artwork

    def _remember(self, external_id: str, artwork: ArticArtwork | None) -> None:
        if self.cache_ttl_seconds <= 0:
            return
        self._cache[external_id] = CachedArtwork(
            value=artwork,
            expires_at=monotonic() + self.cache_ttl_seconds,
        )


def get_artic_client(settings: Settings = Depends(get_settings)) -> ArticClient:
    return ArticClient(
        settings.artic_base_url,
        cache_ttl_seconds=settings.artic_cache_ttl_seconds,
    )
