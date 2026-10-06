"""
UI tests for the Playwright TodoMVC demo app.
"""

import pytest
from playwright.sync_api import expect

from domain.ui.ui_service import UiService
from test_scripts.utils.test_data import load_test_data

TODO_ITEMS = [str(value) for value in load_test_data()["ui"]["todo_items"]]

pytestmark = [pytest.mark.ui, pytest.mark.regression]


@pytest.mark.smoke
@pytest.mark.scenario("UI-TODO-0001")
def test_todo_app_opens(ui_service: UiService) -> None:
    """The app loads and offers the new-item input."""
    todo_page = ui_service.open_todo_app()

    assert "TodoMVC" in ui_service.title()
    expect(todo_page.new_todo_input).to_be_visible()


@pytest.mark.scenario("UI-TODO-0002")
def test_added_items_are_listed_in_order(ui_service: UiService) -> None:
    """Items appear in insertion order and the counter matches."""
    todo_page = ui_service.open_todo_app()

    todo_page.add(*TODO_ITEMS)

    expect(todo_page.item_titles).to_have_text(TODO_ITEMS)
    expect(todo_page.counter).to_have_text(f"{len(TODO_ITEMS)} items left")


@pytest.mark.scenario("UI-TODO-0003")
@pytest.mark.parametrize("completed_item", TODO_ITEMS)
def test_filters_split_active_and_completed_items(ui_service: UiService, completed_item: str) -> None:
    """Completing one item moves it from Active to Completed."""
    todo_page = ui_service.open_todo_app()
    todo_page.add(*TODO_ITEMS)

    todo_page.complete(completed_item)

    todo_page.show("Completed")
    expect(todo_page.item_titles).to_have_text([completed_item])
    todo_page.show("Active")
    expect(todo_page.item_titles).to_have_text([item for item in TODO_ITEMS if item != completed_item])
