"""
Page object for the Playwright TodoMVC demo app.
"""

from __future__ import annotations

from playwright.sync_api import Locator

from adapters.playwright_adapter import PlaywrightAdapter


class TodoPage:
    """
    TodoMVC page at `<UI_BASE_URL>/todomvc/`.
    """

    PATH = "/todomvc/"

    def __init__(self, adapter: PlaywrightAdapter) -> None:
        """
        Initialize the page object.

        :param adapter: Mandatory, Playwright adapter.
        """
        self.adapter = adapter

    def open(self) -> TodoPage:
        """
        Navigate to the app.

        :return: Self, for chaining.
        """
        self.adapter.open(self.PATH)
        return self

    @property
    def new_todo_input(self) -> Locator:
        """Input used to create todos."""
        return self.adapter.by_placeholder("What needs to be done?")

    @property
    def item_titles(self) -> Locator:
        """Titles of the visible todo items."""
        return self.adapter.by_test_id("todo-title")

    @property
    def counter(self) -> Locator:
        """The "N items left" counter."""
        return self.adapter.by_test_id("todo-count")

    def add(self, *titles: str) -> None:
        """
        Add todo items in order.

        :param titles: Mandatory, Titles to add.
        """
        for title in titles:
            self.new_todo_input.fill(title)
            self.new_todo_input.press("Enter")

    def complete(self, title: str) -> None:
        """
        Mark a todo item as completed.

        :param title: Mandatory, Title of the item.
        """
        self.adapter.by_test_id("todo-item").filter(has_text=title).get_by_role("checkbox").check()

    def show(self, filter_name: str) -> None:
        """
        Apply a list filter.

        :param filter_name: Mandatory, One of "All", "Active", "Completed".
        """
        self.adapter.by_role("link", filter_name).click()
