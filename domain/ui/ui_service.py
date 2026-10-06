"""
Domain service for UI operations.
"""

from __future__ import annotations

from adapters.playwright_adapter import AccessibilityViolation, PlaywrightAdapter
from domain.ui.pages.fruits_page import FruitsPage
from domain.ui.pages.todo_page import TodoPage


class UiService:
    """
    Entry point from tests into the UI domain: opens apps and returns page objects.
    """

    def __init__(self, playwright_adapter: PlaywrightAdapter) -> None:
        """
        Initialize the UI service.

        :param playwright_adapter: Mandatory, Playwright adapter instance.
        """
        self.playwright_adapter = playwright_adapter

    def open_todo_app(self, seeded_items: list[str] | None = None) -> TodoPage:
        """
        Open the TodoMVC app, optionally pre-loaded with items.

        :param seeded_items: Optional, Titles to put into the app's storage before it loads.
        :return: TodoPage page object.
        """
        page = TodoPage(self.playwright_adapter)
        if seeded_items:
            page.seed(seeded_items)
        return page.open()

    def fruits_page(self) -> FruitsPage:
        """
        Get the fruit list page object without opening it, so network behaviour can be set up first.

        :return: FruitsPage page object.
        """
        return FruitsPage(self.playwright_adapter)

    def accessibility_violations(self, min_impact: str = "serious") -> list[AccessibilityViolation]:
        """
        Scan the current page with axe-core.

        :param min_impact: Optional, Lowest impact to report.
        :return: Violations at or above the given impact.
        """
        return self.playwright_adapter.accessibility_violations(min_impact)

    def title(self) -> str:
        """
        Get the current page title.

        :return: Page title.
        """
        return self.playwright_adapter.title()
