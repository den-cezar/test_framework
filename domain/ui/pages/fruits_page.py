"""
Page object for the Playwright api-mocking demo: a list rendered from `GET /api/v1/fruits`.
"""

from __future__ import annotations

from playwright.sync_api import Locator

from adapters.playwright_adapter import PlaywrightAdapter
from domain.api.models import FRUITS, Fruit


class FruitsPage:
    """
    Fruit list at `<UI_BASE_URL>/api-mocking/`. Network behaviour must be set up before `open()`.
    """

    PATH = "/api-mocking/"
    API_PATTERN = "**/api/v1/fruits"

    def __init__(self, adapter: PlaywrightAdapter) -> None:
        """
        Initialize the page object.

        :param adapter: Mandatory, Playwright adapter.
        """
        self.adapter = adapter

    def open(self) -> FruitsPage:
        """
        Navigate to the app.

        :return: Self, for chaining.
        """
        self.adapter.open(self.PATH)
        return self

    @property
    def heading(self) -> Locator:
        """Page heading, rendered regardless of the API result."""
        return self.adapter.by_role("heading", "Render a List of Fruits")

    @property
    def items(self) -> Locator:
        """Rendered fruit names."""
        return self.adapter.by_role_any("listitem")

    def serve_fruits(self, fruits: list[Fruit]) -> None:
        """
        Replace the API response with the given fruits.

        :param fruits: Mandatory, Fruits to return.
        """
        self.adapter.mock_response(self.API_PATTERN, 200, FRUITS.dump_python(fruits))

    def fail_api(self, status: int) -> None:
        """
        Make the API return an error.

        :param status: Mandatory, HTTP error status.
        """
        self.adapter.mock_response(self.API_PATTERN, status)

    def slow_down_api(self, delay_seconds: float) -> None:
        """
        Add latency to the real API.

        :param delay_seconds: Mandatory, Added latency.
        """
        self.adapter.delay_response(self.API_PATTERN, delay_seconds)

    def append_to_real_response(self, fruit: Fruit) -> None:
        """
        Let the real API answer, then append one fruit (validating the real body against the contract).

        :param fruit: Mandatory, Fruit to append.
        """
        self.adapter.modify_json_response(
            self.API_PATTERN, lambda body: [*FRUITS.dump_python(FRUITS.validate_python(body)), fruit.model_dump()]
        )
