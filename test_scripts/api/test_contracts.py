"""
Contract tests: responses must match the pydantic models in domain/api/models.py.
"""

import pytest

from domain.api.api_service import ApiService
from domain.api.models import REQUIRED_IDENTITY_CLAIMS
from test_scripts.utils.test_data import load_test_data

pytestmark = [pytest.mark.api, pytest.mark.contract, pytest.mark.regression]


@pytest.mark.smoke
@pytest.mark.scenario("API-CONTRACT-0001")
def test_identity_claims_match_contract(api_service: ApiService) -> None:
    """Parsing enforces the claim shape; here we also require the claims consumers rely on."""
    claims = api_service.get_identity_claim_list()

    claim_types = {claim.type for claim in claims}
    assert REQUIRED_IDENTITY_CLAIMS <= claim_types, f"missing: {sorted(REQUIRED_IDENTITY_CLAIMS - claim_types)}"


@pytest.mark.scenario("API-CONTRACT-0002")
def test_status_document_matches_contract(api_service: ApiService) -> None:
    """Statuspage.io response parses into ServiceStatus (unknown fields or indicator values fail)."""
    status = api_service.get_service_status(str(load_test_data()["api"]["public_health_url"]))

    assert status.page.name == "GitHub"
    assert status.status.description
