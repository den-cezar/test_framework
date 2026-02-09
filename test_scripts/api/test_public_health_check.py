"""
Public health check tests.
"""

import httpx
import pytest

from domain.api.api_service import ApiService
from test_scripts.utils.test_data import load_test_data


@pytest.mark.api
def test_public_github_health_check(api_service: ApiService) -> None:
    """Scenarios: API-PUBLIC-HEALTH-0001"""
    test_data = load_test_data()
    url_value = str(test_data["api"]["public_health_url"])

    try:
        status_code = api_service.public_health_check(url_value)
    except httpx.RequestError as exc:
        pytest.skip(f"Public health endpoint unavailable: {exc}")

    assert status_code == 200
