"""
Playwright adapter for UI interactions.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Locator, Page, Route

from core.logging.logger import Logger

logger = Logger.get_logger("PlaywrightAdapter")

IMPACT_ORDER = ("minor", "moderate", "serious", "critical")


@dataclass(frozen=True)
class AccessibilityViolation:
    """One axe-core rule violation."""

    rule_id: str
    impact: str
    help: str
    nodes: int


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

    def by_role_any(self, role: str) -> Locator:
        """
        Locate all elements with an ARIA role.

        :param role: Mandatory, ARIA role (e.g. "listitem").
        :return: Locator.
        """
        return self.page.get_by_role(role)  # type: ignore[arg-type]

    def seed_local_storage(self, key: str, value: Any) -> None:
        """
        Set a localStorage entry before any page script runs (applies to later navigations).

        :param key: Mandatory, Storage key.
        :param value: Mandatory, JSON-serialisable value, stored as a JSON string.
        """
        script = f"window.localStorage.setItem({json.dumps(key)}, {json.dumps(json.dumps(value))});"
        self.page.add_init_script(script)

    def mock_response(self, url_pattern: str, status: int, json_body: Any = None) -> None:
        """
        Answer matching requests without reaching the backend.

        :param url_pattern: Mandatory, Glob URL pattern.
        :param status: Mandatory, HTTP status to return.
        :param json_body: Optional, JSON body; None returns an empty body.
        """
        logger.info("Mocking %s with HTTP %s", url_pattern, status)
        body = json.dumps(json_body) if json_body is not None else ""
        self.page.route(
            url_pattern, lambda route: route.fulfill(status=status, body=body, content_type="application/json")
        )

    def delay_response(self, url_pattern: str, delay_seconds: float) -> None:
        """
        Hold matching requests for a while, then let them reach the backend.

        :param url_pattern: Mandatory, Glob URL pattern.
        :param delay_seconds: Mandatory, Added latency.
        """
        logger.info("Delaying %s by %.1fs", url_pattern, delay_seconds)

        def handler(route: Route) -> None:
            time.sleep(delay_seconds)
            route.continue_()

        self.page.route(url_pattern, handler)

    def modify_json_response(self, url_pattern: str, transform: Callable[[Any], Any]) -> None:
        """
        Fetch the real response for matching requests and return a transformed JSON body.

        :param url_pattern: Mandatory, Glob URL pattern.
        :param transform: Mandatory, Function from the real JSON body to the body to return.
        """
        logger.info("Modifying responses of %s", url_pattern)

        def handler(route: Route) -> None:
            response = route.fetch()
            route.fulfill(response=response, json=transform(response.json()))

        self.page.route(url_pattern, handler)

    def accessibility_violations(self, min_impact: str = "serious") -> list[AccessibilityViolation]:
        """
        Run axe-core on the current page.

        :param min_impact: Optional, Lowest impact to report (minor, moderate, serious, critical).
        :return: Violations at or above the given impact.
        """
        threshold = IMPACT_ORDER.index(min_impact)
        violations = Axe().run(self.page).response["violations"]
        return [
            AccessibilityViolation(
                rule_id=item["id"], impact=item["impact"], help=item["help"], nodes=len(item["nodes"])
            )
            for item in violations
            if item.get("impact") in IMPACT_ORDER and IMPACT_ORDER.index(item["impact"]) >= threshold
        ]
