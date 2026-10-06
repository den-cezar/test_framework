"""
UI resilience tests: the fruit list is driven by mocked, modified, failing and slow API responses.
"""

import pytest
from playwright.sync_api import expect

from domain.api.models import Fruit
from domain.ui.ui_service import UiService

pytestmark = [pytest.mark.ui, pytest.mark.network, pytest.mark.regression]


@pytest.mark.smoke
@pytest.mark.scenario("UI-MOCK-0001")
def test_list_renders_exactly_the_api_data(ui_service: UiService) -> None:
    """A fully mocked API makes the UI test independent of backend data."""
    fruits = [Fruit(name="Feijoa", id=901), Fruit(name="Rambutan", id=902)]
    page = ui_service.fruits_page()
    page.serve_fruits(fruits)

    page.open()

    expect(page.items).to_have_text([fruit.name for fruit in fruits])


@pytest.mark.scenario("UI-MOCK-0002")
def test_item_added_to_real_response_is_rendered(ui_service: UiService) -> None:
    """The real response is kept (and contract-checked); only one extra item is injected."""
    page = ui_service.fruits_page()
    page.append_to_real_response(Fruit(name="Injected Durian", id=999))

    page.open()

    expect(page.items.last).to_have_text("Injected Durian")
    expect(page.items).not_to_have_count(1)


@pytest.mark.scenario("UI-MOCK-0003")
@pytest.mark.parametrize("status", [500, 503])
def test_failing_api_leaves_page_usable(ui_service: UiService, status: int) -> None:
    """Characterises current behaviour: on API errors the page renders, just without a list."""
    page = ui_service.fruits_page()
    page.fail_api(status)

    page.open()

    expect(page.heading).to_be_visible()
    expect(page.items).to_have_count(0)


@pytest.mark.scenario("UI-MOCK-0004")
def test_slow_api_still_renders_list(ui_service: UiService) -> None:
    """Two seconds of added latency stays within the default assertion timeout."""
    page = ui_service.fruits_page()
    page.slow_down_api(2)

    page.open()

    expect(page.items.first).to_be_visible()
