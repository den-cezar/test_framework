"""
Domain service for UI operations.
"""

from __future__ import annotations

from adapters.playwright_adapter import PlaywrightAdapter
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

    def open_todo_app(self) -> TodoPage:
        """
        Open the TodoMVC app.

        :return: TodoPage page object.
        """
        return TodoPage(self.playwright_adapter).open()

    def title(self) -> str:
        """
        Get the current page title.

        :return: Page title.
        """
        return self.playwright_adapter.title()
