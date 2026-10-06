"""
Negative authentication tests for the protected API and the identity provider.
"""

import base64
import dataclasses
import json
from pathlib import Path

import pytest

from core.auth.oauth_client import OAuthClient
from core.auth.token_cache import SharedTokenCache
from core.config.settings import FrameworkSettings
from core.errors import AuthError
from domain.api.api_service import ApiService

pytestmark = [pytest.mark.api, pytest.mark.security, pytest.mark.regression]


def _tamper(token: str) -> str:
    """Change the client_id claim while keeping the original signature."""
    header, payload, signature = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["client_id"] = "attacker"
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"{header}.{forged}.{signature}"


def _isolated_oauth_client(settings: FrameworkSettings, tmp_path: Path, **overrides: str) -> OAuthClient:
    """OAuth client with one modified client config and its own cache, so no valid token is reused."""
    name, config = settings.resolve_oauth_client()
    broken = dataclasses.replace(settings, oauth_clients={name: dataclasses.replace(config, **overrides)})
    return OAuthClient(broken, SharedTokenCache(tmp_path.joinpath("cache.json")))


@pytest.mark.smoke
@pytest.mark.scenario("API-AUTH-NEG-0001")
@pytest.mark.parametrize(
    "authorization",
    [
        pytest.param(None, id="no-header"),
        pytest.param("Bearer not-a-jwt", id="malformed"),
        pytest.param("Basic bTJtOnNlY3JldA==", id="wrong-scheme"),
        pytest.param("tampered", id="tampered-signature"),
    ],
)
def test_protected_api_rejects_invalid_credentials(
    api_service: ApiService, oauth_client: OAuthClient, authorization: str | None
) -> None:
    """Missing, malformed, wrong-scheme and tampered tokens must all get 401."""
    if authorization == "tampered":
        authorization = f"Bearer {_tamper(oauth_client.get_access_token())}"

    assert api_service.identity_status_with_authorization(authorization) == 401


@pytest.mark.scenario("API-AUTH-NEG-0002")
def test_identity_provider_rejects_wrong_secret(framework_settings: FrameworkSettings, tmp_path: Path) -> None:
    """Wrong client secret must fail with invalid_client."""
    client = _isolated_oauth_client(framework_settings, tmp_path, client_secret="definitely-wrong")

    with pytest.raises(AuthError, match="400.*invalid_client"):
        client.get_access_token()
    client.close()


@pytest.mark.scenario("API-AUTH-NEG-0003")
def test_identity_provider_rejects_unknown_scope(framework_settings: FrameworkSettings, tmp_path: Path) -> None:
    """A scope the client is not allowed to request must fail with invalid_scope."""
    client = _isolated_oauth_client(framework_settings, tmp_path)

    with pytest.raises(AuthError, match="400.*invalid_scope"):
        client.get_access_token(scope_value="scope-that-does-not-exist")
    client.close()
