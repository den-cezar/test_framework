"""
Page object for the Playwright TodoMVC demo app.
"""

from __future__ import annotations

import uuid

from playwright.sync_api import Locator

from adapters.playwright_adapter import PlaywrightAdapter


class TodoPage:
    """
    TodoMVC page at `<UI_BASE_URL>/todomvc/`.
    """

    PATH = "/todomvc/"
    STORAGE_KEY = "react-todos"

    def __init__(self, adapter: PlaywrightAdapter) -> None:
        """
        Initialize the page object.

        :param adapter: Mandatory, Playwright adapter.
        """
        self.adapter = adapter

    def seed(self, titles: list[str]) -> TodoPage:
        """
        Pre-load items through the app's localStorage instead of the UI. Call before `open()`.

        :param titles: Mandatory, Item titles, all active.
        :return: Self, for chaining.
        """
        items = [{"id": str(uuid.uuid4()), "title": title, "completed": False} for title in titles]
        self.adapter.seed_local_storage(self.STORAGE_KEY, items)
        return self

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
