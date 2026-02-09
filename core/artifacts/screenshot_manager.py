"""
Screenshot management for UI test failures.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.logging.logger import Logger


class ScreenshotManager:
    """
    Manage screenshot capture and storage.
    """

    def __init__(self, output_root: Path, timezone_name: str) -> None:
        """
        Initialize the screenshot manager.

        :param output_root: Mandatory, Root output directory for artifacts.
        :param timezone_name: Mandatory, Timezone name (UTC or LOCAL).
        """
        logger = Logger.get_logger("Artifacts")
        logger.debug("Initializing ScreenshotManager.")

        if not isinstance(output_root, Path):
            raise ValueError("output_root must be a Path.")
        if timezone_name not in {"UTC", "LOCAL"}:
            raise ValueError("timezone_name must be UTC or LOCAL.")

        self.output_root = output_root
        self.timezone_name = timezone_name

    def capture(self, page_value: Any, test_name: str) -> Path:
        """
        Capture a screenshot using the provided page object.

        :param page_value: Mandatory, UI page object with screenshot method.
        :param test_name: Mandatory, The test name used for artifact path.
        :return: Path to the saved screenshot.
        """
        logger = Logger.get_logger("Artifacts")
        logger.debug("Capturing UI screenshot.")

        if page_value is None or not hasattr(page_value, "screenshot"):
            raise ValueError("page_value must provide a screenshot method.")
        if not isinstance(test_name, str) or not test_name:
            raise ValueError("test_name must be a non-empty string.")

        safe_test_name = self._sanitize_test_name(test_name)
        screenshots_dir = self.output_root.joinpath(safe_test_name, "screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        timestamp = self._get_timestamp_prefix()
        file_name = f"{timestamp}_error_screenshot.png"
        screenshot_path = screenshots_dir.joinpath(file_name)

        page_value.screenshot(path=str(screenshot_path))
        return screenshot_path

    def _sanitize_test_name(self, test_name: str) -> str:
        """
        Sanitize a test name for filesystem paths.

        :param test_name: Mandatory, Test name to sanitize.
        :return: Safe filesystem name.
        """
        safe_chars: list[str] = []
        for char in test_name:
            if char.isalnum() or char in {"-", "_", "."}:
                safe_chars.append(char)
            else:
                safe_chars.append("_")
        return "".join(safe_chars)

    def _get_timestamp_prefix(self) -> str:
        """
        Get a timestamp prefix for the screenshot filename.

        :return: Timestamp string.
        """
        logger = Logger.get_logger("Artifacts")
        logger.debug("Generating screenshot timestamp.")

        if self.timezone_name == "UTC":
            now_value = datetime.now(UTC)
        else:
            now_value = datetime.now()
        return now_value.strftime("%Y%m%d_%H%M%S")
