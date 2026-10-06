"""
OAuth client-credentials tests across all configured clients.
"""

import pytest

from core.auth.oauth_client import OAuthClient
from core.config.settings import FrameworkSettings

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.mark.smoke
def test_token_is_issued_for_each_configured_client(
    oauth_client: OAuthClient, framework_settings: FrameworkSettings, subtests: pytest.Subtests
) -> None:
    """Scenarios: API-OAUTH-CLIENTS-0001"""
    for client_name in sorted(framework_settings.oauth_clients):
        with subtests.test(client=client_name):
            assert oauth_client.get_access_token(client_name=client_name)


def test_token_is_reused_from_cache(oauth_client: OAuthClient) -> None:
    """Scenarios: API-OAUTH-CLIENTS-0002"""
    assert oauth_client.get_access_token() == oauth_client.get_access_token()
