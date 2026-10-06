"""
Hybrid tests: the API arranges or supplies data, the UI verifies it.
"""

import pytest
from playwright.sync_api import expect

from domain.api.api_service import ApiService
from domain.ui.ui_service import UiService

pytestmark = [pytest.mark.api, pytest.mark.ui, pytest.mark.hybrid, pytest.mark.regression]


@pytest.mark.smoke
@pytest.mark.scenario("HYBRID-0001")
def test_api_data_is_displayed_in_ui(api_service: ApiService, ui_service: UiService) -> None:
    """Claims from the protected API are seeded into the app's storage and must render unchanged."""
    claims = api_service.get_identity_claims()
    titles = [f"{claim}: {claims[claim]}" for claim in ("client_id", "scope", "iss")]

    todo_page = ui_service.open_todo_app(seeded_items=titles)

    expect(todo_page.item_titles).to_have_text(titles)
    expect(todo_page.counter).to_have_text(f"{len(titles)} items left")
