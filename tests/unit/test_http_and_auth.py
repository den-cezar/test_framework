from urllib.parse import parse_qs

import httpx
import pytest

from adapters.http_client import HttpClient
from core.auth.oauth_client import OAuthClient
from core.auth.token_cache import SharedTokenCache
from core.config.settings import FrameworkSettings
from core.errors import AuthError


def _token_endpoint(requests: list[httpx.Request], status_code: int = 200, body: object = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            status_code, json=body if body is not None else {"access_token": "abc", "expires_in": 3600}
        )

    return httpx.MockTransport(handler)


def _oauth_client(settings: FrameworkSettings, transport: httpx.MockTransport) -> OAuthClient:
    return OAuthClient(settings, SharedTokenCache(settings.token_cache_path), http=httpx.Client(transport=transport))


def test_client_credentials_request_and_caching(settings: FrameworkSettings) -> None:
    requests: list[httpx.Request] = []
    client = _oauth_client(settings, _token_endpoint(requests))

    assert client.get_access_token() == "abc"
    assert client.get_access_token() == "abc"

    assert len(requests) == 1
    form = parse_qs(requests[0].content.decode())
    assert str(requests[0].url) == settings.oauth_token_url
    assert form == {
        "grant_type": ["client_credentials"],
        "client_id": ["id-a"],
        "client_secret": ["secret-a"],
        "scope": ["api"],
    }


def test_scope_override_uses_separate_cache_entry(settings: FrameworkSettings) -> None:
    requests: list[httpx.Request] = []
    client = _oauth_client(settings, _token_endpoint(requests))

    client.get_access_token()
    client.get_access_token(scope_value="other")

    assert len(requests) == 2
    assert parse_qs(requests[1].content.decode())["scope"] == ["other"]


@pytest.mark.parametrize(
    ("status_code", "body", "message"),
    [
        (401, {"error": "invalid_client"}, "Token request failed: 401"),
        (200, {"access_token": "", "expires_in": 3600}, "Invalid token response"),
        (200, {"access_token": "abc", "expires_in": 0}, "Invalid token response"),
    ],
)
def test_bad_token_responses_raise_auth_error(
    settings: FrameworkSettings, status_code: int, body: object, message: str
) -> None:
    client = _oauth_client(settings, _token_endpoint([], status_code, body))

    with pytest.raises(AuthError, match=message):
        client.get_access_token()


def test_http_client_sends_bearer_token_to_base_url(settings: FrameworkSettings) -> None:
    api_requests: list[httpx.Request] = []

    def api(request: httpx.Request) -> httpx.Response:
        api_requests.append(request)
        return httpx.Response(200, json={"ok": True})

    http = HttpClient(settings, _oauth_client(settings, _token_endpoint([])), transport=httpx.MockTransport(api))

    response = http.request("get", "/api/test", json_body={"q": 1})
    http.close()

    assert response.json() == {"ok": True}
    assert str(api_requests[0].url) == "https://api.example.test/api/test"
    assert api_requests[0].method == "GET"
    assert api_requests[0].headers["Authorization"] == "Bearer abc"


def test_http_client_public_request_has_no_auth(settings: FrameworkSettings) -> None:
    token_requests: list[httpx.Request] = []
    api_requests: list[httpx.Request] = []

    def api(request: httpx.Request) -> httpx.Response:
        api_requests.append(request)
        return httpx.Response(204)

    http = HttpClient(
        settings, _oauth_client(settings, _token_endpoint(token_requests)), transport=httpx.MockTransport(api)
    )

    http.request_public("GET", "https://status.example.test/health")

    assert str(api_requests[0].url) == "https://status.example.test/health"
    assert "Authorization" not in api_requests[0].headers
    assert token_requests == []
