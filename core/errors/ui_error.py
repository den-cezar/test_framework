"""
UI error handling with screenshot capture.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.artifacts.screenshot_manager import ScreenshotManager
from core.errors.framework_error import FrameworkError
from core.logging.logger import Logger


class UiError(FrameworkError):
    """
    UI error that captures a screenshot on creation.
    """

    def __init__(self, message: str, screenshot_manager: ScreenshotManager, page_value: Any, test_name: str) -> None:
        """
        Initialize the UI error and capture a screenshot.

        :param message: Mandatory, Error message.
        :param screenshot_manager: Mandatory, Screenshot manager.
        :param page_value: Mandatory, UI page object.
        :param test_name: Mandatory, Test name for artifact path.
        """
        logger = Logger.get_logger("UiError")
        logger.debug("Creating UiError and capturing screenshot.")

        if not isinstance(screenshot_manager, ScreenshotManager):
            raise ValueError("screenshot_manager must be a ScreenshotManager instance.")
        if page_value is None or not hasattr(page_value, "screenshot"):
            raise ValueError("page_value must provide a screenshot method.")
        if not isinstance(test_name, str) or not test_name:
            raise ValueError("test_name must be a non-empty string.")

        screenshot_path = screenshot_manager.capture(page_value, test_name)
        self.screenshot_path_value: Path = screenshot_path
        super().__init__(message, screenshot_path)
