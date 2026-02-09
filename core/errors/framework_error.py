"""
Error handling primitives for the new test framework.
"""

from __future__ import annotations

from pathlib import Path

from core.logging.logger import Logger


class FrameworkError(Exception):
    """
    Base framework error with optional screenshot path.
    """

    def __init__(self, message: str, screenshot_path: Path | None = None) -> None:
        """
        Initialize the framework error.

        :param message: Mandatory, Error message.
        :param screenshot_path: Optional, Path to a captured screenshot.
        """
        logger = Logger.get_logger("Errors")
        logger.debug("Creating FrameworkError instance.")

        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string.")
        if screenshot_path is not None and not isinstance(screenshot_path, Path):
            raise ValueError("screenshot_path must be a Path or None.")

        super().__init__(message)
        self.screenshot_path = screenshot_path
