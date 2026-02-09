"""
OAuth demo tests using multiple clients.
"""

import pytest

from core.auth.oauth_client import OAuthClient
from core.config.settings import FrameworkSettings


def _skip_reason(framework_settings: FrameworkSettings) -> str:
    """Determine the reason for skipping tests based on the framework settings."""
    if not framework_settings.oauth_clients:
        return "No OAuth clients configured."
    return ""


@pytest.mark.api
def test_oauth_token_first_client(oauth_client: OAuthClient, framework_settings: FrameworkSettings) -> None:
    """Scenarios: API-OAUTH-CLIENTS-0001"""
    reason = _skip_reason(framework_settings)
    if reason:
        pytest.skip(reason)

    client_name = sorted(framework_settings.oauth_clients.keys())[0]
    token = oauth_client.get_access_token(client_name=client_name)
    assert token


@pytest.mark.api
def test_oauth_token_second_client(oauth_client: OAuthClient, framework_settings: FrameworkSettings) -> None:
    """Scenarios: API-OAUTH-CLIENTS-0002"""
    reason = _skip_reason(framework_settings)
    if reason:
        pytest.skip(reason)

    client_name = sorted(framework_settings.oauth_clients.keys())[1]
    token = oauth_client.get_access_token(client_name=client_name)
    assert token
