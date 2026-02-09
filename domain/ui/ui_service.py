"""
Domain service for UI operations.
"""

from __future__ import annotations

from pathlib import Path

from adapters.playwright_adapter import PlaywrightAdapter
from core.artifacts.screenshot_manager import ScreenshotManager
from core.logging.logger import Logger


class UiService:
    """
    Domain UI service wrapper.
    """

    def __init__(self, playwright_adapter: PlaywrightAdapter, screenshot_manager: ScreenshotManager) -> None:
        """
        Initialize the UI service.

        :param playwright_adapter: Mandatory, Playwright adapter instance.
        :param screenshot_manager: Mandatory, Screenshot manager.
        """
        logger = Logger.get_logger("UiService")
        logger.debug("Initializing UiService.")

        if not isinstance(playwright_adapter, PlaywrightAdapter):
            raise ValueError("playwright_adapter must be a PlaywrightAdapter instance.")
        if not isinstance(screenshot_manager, ScreenshotManager):
            raise ValueError("screenshot_manager must be a ScreenshotManager instance.")

        self.playwright_adapter = playwright_adapter
        self.screenshot_manager = screenshot_manager

    def capture_error_screenshot(self, test_name: str) -> Path:
        """
        Capture a UI error screenshot.

        :param test_name: Mandatory, Test name for the screenshot.
        :return: Path to the saved screenshot.
        """
        logger = Logger.get_logger("UiService")
        logger.debug("Capturing UI error screenshot.")

        return self.screenshot_manager.capture(self.playwright_adapter.page, test_name)
