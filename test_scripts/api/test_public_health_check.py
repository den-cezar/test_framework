"""
Public health check tests.
"""

import pytest

from domain.api.api_service import ApiService
from test_scripts.utils.test_data import load_test_data

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.mark.scenario("API-PUBLIC-HEALTH-0001")
def test_public_github_health_check(api_service: ApiService) -> None:
    """The public status endpoint answers with a parseable, known status."""
    status = api_service.get_service_status(str(load_test_data()["api"]["public_health_url"]))

    assert status.status.indicator in {"none", "minor", "major", "critical", "maintenance"}
