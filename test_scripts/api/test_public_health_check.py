"""
Public health check tests.
"""

import pytest

from domain.api.api_service import ApiService
from test_scripts.utils.test_data import load_test_data

pytestmark = [pytest.mark.api, pytest.mark.regression]


def test_public_github_health_check(api_service: ApiService) -> None:
    """Scenarios: API-PUBLIC-HEALTH-0001"""
    url_value = str(load_test_data()["api"]["public_health_url"])

    assert api_service.public_health_check(url_value) == 200
