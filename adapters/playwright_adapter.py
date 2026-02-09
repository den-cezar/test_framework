"""
Playwright adapter for UI interactions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.logging.logger import Logger


class PlaywrightAdapter:
    """
    Adapter wrapper for Playwright interactions.
    """

    def __init__(self, page_value: Any) -> None:
        """
        Initialize the Playwright adapter.

        :param page_value: Mandatory, Playwright page instance.
        """
        logger = Logger.get_logger("PlaywrightAdapter")
        logger.debug("Initializing Playwright adapter.")

        if page_value is None:
            raise ValueError("page_value must be provided.")
        self.page = page_value

    def capture_screenshot(self, path_value: Path) -> None:
        """
        Capture a screenshot to the specified path.

        :param path_value: Mandatory, Path to save the screenshot.
        """
        logger = Logger.get_logger("PlaywrightAdapter")
        logger.debug("Capturing screenshot.")

        if not isinstance(path_value, Path):
            raise ValueError("path_value must be a Path.")

        self.page.screenshot(path=str(path_value))
