"""
Playwright adapter for UI interactions.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page

from core.logging.logger import Logger

logger = Logger.get_logger("PlaywrightAdapter")


class PlaywrightAdapter:
    """
    Thin wrapper over a Playwright page that resolves paths against UI_BASE_URL.
    """

    def __init__(self, page: Page, base_url: str) -> None:
        """
        Initialize the Playwright adapter.

        :param page: Mandatory, Playwright page instance.
        :param base_url: Mandatory, Base URL of the UI under test.
        """
        self.page = page
        self.base_url = base_url.rstrip("/")

    def open(self, path_value: str = "/") -> None:
        """
        Navigate to a path under the base URL.

        :param path_value: Optional, Path relative to the base URL.
        """
        url_value = f"{self.base_url}/{path_value.lstrip('/')}"
        logger.info("Opening %s", url_value)
        self.page.goto(url_value, wait_until="domcontentloaded")

    def title(self) -> str:
        """
        Get the document title.

        :return: Page title.
        """
        return self.page.title()

    def by_test_id(self, test_id: str) -> Locator:
        """
        Locate elements by their data-testid attribute.

        :param test_id: Mandatory, Test id value.
        :return: Locator.
        """
        return self.page.get_by_test_id(test_id)

    def by_placeholder(self, text: str) -> Locator:
        """
        Locate an input by its placeholder text.

        :param text: Mandatory, Placeholder text.
        :return: Locator.
        """
        return self.page.get_by_placeholder(text)

    def by_role(self, role: str, name: str) -> Locator:
        """
        Locate an element by ARIA role and accessible name.

        :param role: Mandatory, ARIA role (e.g. "link", "button").
        :param name: Mandatory, Accessible name.
        :return: Locator.
        """
        return self.page.get_by_role(role, name=name)  # type: ignore[arg-type]
