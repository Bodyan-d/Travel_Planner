import httpx

from app.services.artic import ArticClient


def test_artic_client_caches_successful_artwork_response() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={"data": {"id": 123, "title": "Cached artwork", "api_link": "https://example.test/123"}},
        )

    client = ArticClient(
        "https://api.example.test",
        cache_ttl_seconds=300,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    first = client.get_artwork("123")
    second = client.get_artwork("123")

    assert calls == 1
    assert first == second
    assert first is not None
    assert first.title == "Cached artwork"


def test_artic_client_caches_missing_artwork_response() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404, json={"error": "Not found"})

    client = ArticClient(
        "https://api.example.test",
        cache_ttl_seconds=300,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.get_artwork("404") is None
    assert client.get_artwork("404") is None
    assert calls == 1


def test_artic_client_can_disable_cache() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"data": {"id": 123, "title": f"Artwork {calls}"}})

    client = ArticClient(
        "https://api.example.test",
        cache_ttl_seconds=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    first = client.get_artwork("123")
    second = client.get_artwork("123")

    assert calls == 2
    assert first is not None
    assert second is not None
    assert first.title == "Artwork 1"
    assert second.title == "Artwork 2"
