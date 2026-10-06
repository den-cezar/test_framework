"""
Custom logging utilities for the new test framework.
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import TracebackType


class NewlineAfterExceptionFormatter(logging.Formatter):
    """
    Formatter that adds a newline after exceptions.
    """

    def formatException(  # noqa: N802
        self, exception_info: tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None]
    ) -> str:
        """
        Format the exception with a newline at the end.

        :param exception_info: Mandatory, The exception information.
        :return: A string representation of the exception with a newline.
        """
        formatted_exception = super().formatException(exception_info)
        return f"{formatted_exception}\n"


class CurrentTestFilter(logging.Filter):
    """
    Filter that adds the current test name to log records.
    """

    def __init__(self) -> None:
        """
        Initialize the filter with a default test name.
        """
        super().__init__()
        self.test_name = "test_framework"

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add test name to the log record.

        :param record: Mandatory, The log record to filter.
        :return: True to allow the record to be logged.
        """
        record.test_name = self.test_name
        return True


class Logger:
    """
    Per-process logger that writes to the console and to `<test_run_dir>/<worker_id>.log`.
    """

    _instances: dict[str, Logger] = {}

    LOG_FORMAT = "%(asctime)s - [%(worker_id)s] - %(test_name)s - %(levelname)s - %(name)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def get_instance(
        cls, worker_id: str, test_run_dir: Path, console_level: str = "INFO", file_level: str = "DEBUG"
    ) -> Logger:
        """
        Get or create a Logger instance for the specified worker.

        :param worker_id: Mandatory, The ID of the xdist worker (or "master").
        :param test_run_dir: Mandatory, The root directory for test run logs.
        :param console_level: Optional, Console handler level.
        :param file_level: Optional, File handler level.
        :return: The Logger instance for this worker.
        """
        if worker_id not in cls._instances:
            cls._instances[worker_id] = cls(worker_id, test_run_dir, console_level, file_level)
        return cls._instances[worker_id]

    def __init__(self, worker_id: str, test_run_dir: Path, console_level: str, file_level: str) -> None:
        """
        Initialize the Logger instance.

        :param worker_id: Mandatory, The ID of the worker.
        :param test_run_dir: Mandatory, The root directory for test run logs.
        :param console_level: Mandatory, Console handler level.
        :param file_level: Mandatory, File handler level.
        """
        self.worker_id = worker_id
        self.log_file = test_run_dir.joinpath(f"{worker_id}.log")
        self.console_level = console_level
        self.file_level = file_level

        self._logger = logging.getLogger("test_framework")
        self._test_filter = CurrentTestFilter()
        self._handlers: list[logging.Handler] = []
        self._setup_logger()

    def _setup_logger(self) -> None:
        """
        Replace any existing handlers with a file handler and a console handler.
        """
        self._logger.setLevel(logging.DEBUG)
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)

        formatter = NewlineAfterExceptionFormatter(
            self.LOG_FORMAT.replace("%(worker_id)s", self.worker_id), datefmt=self.DATE_FORMAT
        )
        file_handler = logging.FileHandler(self.log_file, mode="a", encoding="UTF-8")
        file_handler.setLevel(self.file_level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.console_level)

        for handler in (file_handler, console_handler):
            handler.setFormatter(formatter)
            handler.addFilter(self._test_filter)
            self._logger.addHandler(handler)
            self._handlers.append(handler)

    @staticmethod
    def get_logger(name_value: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.

        :param name_value: Mandatory, The name of the logger.
        :return: A logger instance for the specified component.
        """
        return logging.getLogger(f"test_framework.{name_value}")

    def set_test_name(self, test_name: str) -> None:
        """
        Set the current test name for logging context.

        :param test_name: Mandatory, The name of the currently running test.
        """
        self._test_filter.test_name = test_name

    def cleanup(self) -> None:
        """
        Close and detach the handlers created by this instance.
        """
        for handler in self._handlers:
            handler.close()
            self._logger.removeHandler(handler)
        self._handlers.clear()
        Logger._instances.pop(self.worker_id, None)
