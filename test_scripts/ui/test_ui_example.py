"""
UI example tests for the new framework.
"""

import pytest
from playwright.sync_api import Page

from test_scripts.utils.test_data import load_test_data

TEST_DATA = load_test_data()
GOOGLE_QUERIES = [str(value) for value in TEST_DATA["ui"]["google_queries"]]


@pytest.mark.ui
@pytest.mark.parametrize("query_value", GOOGLE_QUERIES)
def test_ui_google_search(playwright_page: Page, query_value: str) -> None:
    """Scenarios: UI-JIRA-0002-002"""
    try:
        playwright_page.goto("https://www.google.com", wait_until="domcontentloaded")
    except Exception as exc:
        pytest.xfail(f"Google is not reachable: {exc}")

    # Accept consent screen if shown.
    accept_all_button = playwright_page.get_by_role("button", name="Accept all")
    if accept_all_button.count() == 0:
        accept_all_button = playwright_page.locator("button:has-text('Accept all')")
    if accept_all_button.count() > 0:
        accept_all_button.first.click()
        playwright_page.wait_for_load_state("domcontentloaded")

    search_input = playwright_page.get_by_role("combobox", name="Search")
    if search_input.count() == 0:
        search_input = playwright_page.locator("textarea[name='q']")

    search_input.fill(query_value)
    search_input.press("Enter")
    playwright_page.wait_for_load_state("domcontentloaded")

    assert "google" in playwright_page.title().lower()


@pytest.mark.ui
def test_ui_github_homepage_title(playwright_page: Page) -> None:
    """Scenarios: UI-JIRA-0002-003"""
    try:
        playwright_page.goto("https://github.com", wait_until="domcontentloaded")
    except Exception as exc:
        pytest.skip(f"GitHub is not reachable: {exc}")

    assert "github" in playwright_page.title().lower()
