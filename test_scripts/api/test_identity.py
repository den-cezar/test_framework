"""
Authenticated API tests against the identity provider's protected endpoint.
"""

import pytest

from core.config.settings import FrameworkSettings
from domain.api.api_service import ApiService

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.mark.smoke
@pytest.mark.scenario("API-IDENTITY-0001")
def test_identity_endpoint_echoes_token_claims(api_service: ApiService, framework_settings: FrameworkSettings) -> None:
    """The protected endpoint sees the client id and scope the token was issued for."""
    client_name, client_config = framework_settings.resolve_oauth_client()

    claims = api_service.get_identity_claims(client_name)

    assert claims["client_id"] == client_config.client_id
    assert claims.get("scope") == client_config.scope
