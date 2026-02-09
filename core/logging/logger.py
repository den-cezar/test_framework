"""
Custom logging utilities for the new test framework.
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from types import TracebackType
from typing import Any


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


class TestNameFilter(logging.Filter):
    """
    Filter that adds test name to log records.
    """

    def __init__(self) -> None:
        """
        Initialize the filter with a default test name.
        """
        super().__init__()
        self.test_name = "test_framework"

    def set_test_name(self, test_name: str) -> None:
        """
        Set the current test name.

        :param test_name: Mandatory, The name of the currently running test.
        """
        if not isinstance(test_name, str) or not test_name:
            raise ValueError("test_name must be a non-empty string.")
        self.test_name = test_name

    def filter(self, record_value: logging.LogRecord) -> bool:  # noqa: A003
        """
        Add test name to the log record.

        :param record_value: Mandatory, The log record to filter.
        :return: True to allow the record to be logged.
        """
        record_value.test_name = self.test_name
        return True


class Logger:
    """
    Singleton Logger class for logging test information.
    """

    _instances: dict[str, Logger] = {}
    _lock: threading.Lock = threading.Lock()

    LOG_FORMAT = "%(asctime)s - [%(worker_id)s] - %(test_name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def get_instance(cls, worker_id: str, test_run_dir: Path) -> Logger:
        """
        Get or create a Logger instance for the specified worker.

        :param worker_id: Mandatory, The ID of the worker.
        :param test_run_dir: Mandatory, The root directory for test run logs.
        :return: The Logger instance for this worker.
        """
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker_id must be a non-empty string.")
        if not isinstance(test_run_dir, Path):
            raise ValueError("test_run_dir must be a Path.")

        if worker_id not in cls._instances:
            with cls._lock:
                if worker_id not in cls._instances:
                    cls._instances[worker_id] = cls(worker_id, test_run_dir)
        return cls._instances[worker_id]

    def __init__(self, worker_id: str, test_run_dir: Path) -> None:
        """
        Initialize the Logger instance.

        :param worker_id: Mandatory, The ID of the worker.
        :param test_run_dir: Mandatory, The root directory for test run logs.
        """
        if not isinstance(worker_id, str) or not worker_id:
            raise ValueError("worker_id must be a non-empty string.")
        if not isinstance(test_run_dir, Path):
            raise ValueError("test_run_dir must be a Path.")

        self.worker_id = worker_id
        self.test_run_dir = test_run_dir
        self.log_file = test_run_dir.joinpath(f"{worker_id}.log")
        self.current_test_name = "test_framework"

        self.console_level = os.getenv("LOG_CONSOLE_LEVEL", os.getenv("DEBUG_LEVEL", "INFO"))
        self.file_level = os.getenv("LOG_FILE_LEVEL", "DEBUG")

        self._file_handler: logging.FileHandler | None = None
        self._console_handler: logging.StreamHandler | None = None
        self._logger: logging.Logger | None = None
        self._test_name_filter: TestNameFilter | None = None

        self._setup_logger()

    def _log_debug(self, message: str) -> None:
        """
        Log a debug message if the logger is available.

        :param message: Mandatory, The message to log.
        """
        if self._logger:
            self._logger.debug(message)

    def _setup_logger(self) -> None:
        """
        Set up the root logger with file and console handlers.
        """
        self._logger = logging.getLogger("test_framework")
        self._logger.setLevel(logging.DEBUG)

        if self._logger.hasHandlers():
            for handler in self._logger.handlers[:]:
                handler.close()
                self._logger.removeHandler(handler)

        self._test_name_filter = TestNameFilter()
        self._logger.addFilter(self._test_name_filter)

        self._setup_file_handler()
        self._setup_console_handler()
        self._log_debug("Logger initialized for worker.")

    def _setup_file_handler(self) -> None:
        """
        Set up file logging handler.
        """
        log_format = self.LOG_FORMAT.replace("%(worker_id)s", self.worker_id)
        formatter = NewlineAfterExceptionFormatter(log_format, datefmt=self.DATE_FORMAT)

        self._file_handler = logging.FileHandler(self.log_file, mode="a", encoding="UTF-8")
        self._file_handler.setLevel(self.file_level)
        self._file_handler.setFormatter(formatter)
        if self._test_name_filter:
            self._file_handler.addFilter(self._test_name_filter)
        if self._logger:
            self._logger.addHandler(self._file_handler)

    def _setup_console_handler(self) -> None:
        """
        Set up console logging handler.
        """
        log_format = self.LOG_FORMAT.replace("%(worker_id)s", self.worker_id)
        formatter = NewlineAfterExceptionFormatter(log_format, datefmt=self.DATE_FORMAT)

        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(self.console_level)
        self._console_handler.setFormatter(formatter)
        if self._test_name_filter:
            self._console_handler.addFilter(self._test_name_filter)
        if self._logger:
            self._logger.addHandler(self._console_handler)

    @staticmethod
    def get_logger(name_value: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.

        :param name_value: Mandatory, The name of the logger.
        :return: A logger instance for the specified component.
        """
        if not isinstance(name_value, str) or not name_value:
            raise ValueError("name_value must be a non-empty string.")
        return logging.getLogger(f"test_framework.{name_value}")

    def set_test_name(self, test_name: str) -> None:
        """
        Set the current test name for logging context.

        :param test_name: Mandatory, The name of the currently running test.
        """
        if not isinstance(test_name, str) or not test_name:
            raise ValueError("test_name must be a non-empty string.")
        self.current_test_name = test_name
        if self._test_name_filter:
            self._test_name_filter.set_test_name(test_name)
        self._log_debug("Updated test name for logger.")

    def cleanup(self) -> None:
        """
        Clean up logger resources.
        """
        self._log_debug("Cleaning up logger resources.")
        if self._file_handler:
            self._file_handler.close()
            if self._logger:
                self._logger.removeHandler(self._file_handler)
            self._file_handler = None

        if self._console_handler:
            self._console_handler.close()
            if self._logger:
                self._logger.removeHandler(self._console_handler)
            self._console_handler = None

        if self._logger:
            for handler in self._logger.handlers[:]:
                handler.close()
                self._logger.removeHandler(handler)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a debug message.

        :param message: Mandatory, The message to log.
        :param args: Optional, Variable positional arguments to pass to the logger.
        :param kwargs: Optional, Variable keyword arguments to pass to the logger.
        """
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string.")
        if self._logger:
            self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log an info message.

        :param message: Mandatory, The message to log.
        :param args: Optional, Variable positional arguments to pass to the logger.
        :param kwargs: Optional, Variable keyword arguments to pass to the logger.
        """
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string.")
        if self._logger:
            self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a warning message.

        :param message: Mandatory, The message to log.
        :param args: Optional, Variable positional arguments to pass to the logger.
        :param kwargs: Optional, Variable keyword arguments to pass to the logger.
        """
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string.")
        if self._logger:
            self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log an error message.

        :param message: Mandatory, The message to log.
        :param args: Optional, Variable positional arguments to pass to the logger.
        :param kwargs: Optional, Variable keyword arguments to pass to the logger.
        """
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string.")
        if self._logger:
            self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Log a critical message.

        :param message: Mandatory, The message to log.
        :param args: Optional, Variable positional arguments to pass to the logger.
        :param kwargs: Optional, Variable keyword arguments to pass to the logger.
        """
        if not isinstance(message, str) or not message:
            raise ValueError("message must be a non-empty string.")
        if self._logger:
            self._logger.critical(message, *args, **kwargs)
