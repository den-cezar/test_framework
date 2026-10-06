"""
Per-test artifact storage (screenshots, traces) for the current test run.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol


class SupportsScreenshot(Protocol):
    """
    Anything that can render a PNG screenshot (e.g. a Playwright Page).
    """

    def screenshot(self, *, path: str | Path | None = None) -> bytes: ...


class ArtifactManager:
    """
    Resolve artifact paths under `<test_run_dir>/<sanitized test id>/` and capture screenshots.
    """

    def __init__(self, output_root: Path, timezone_name: str) -> None:
        """
        Initialize the artifact manager.

        :param output_root: Mandatory, Root output directory for the test run.
        :param timezone_name: Mandatory, Timezone for file name timestamps (UTC or LOCAL).
        """
        if timezone_name not in {"UTC", "LOCAL"}:
            raise ValueError("timezone_name must be UTC or LOCAL.")
        self.output_root = output_root
        self.timezone_name = timezone_name

    def test_dir(self, test_name: str) -> Path:
        """
        Return (and create) the artifact directory for a test.

        :param test_name: Mandatory, Pytest node id.
        :return: Directory path.
        """
        directory = self.output_root.joinpath(sanitize_test_name(test_name))
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def capture_screenshot(self, page: SupportsScreenshot, test_name: str) -> tuple[Path, bytes]:
        """
        Capture a screenshot for a test.

        :param page: Mandatory, Object with a `screenshot` method.
        :param test_name: Mandatory, Pytest node id.
        :return: Saved file path and PNG bytes.
        """
        path = self.test_dir(test_name).joinpath(f"{self._timestamp()}_error_screenshot.png")
        return path, page.screenshot(path=path)

    def trace_path(self, test_name: str) -> Path:
        """
        Return the path for a Playwright trace archive.

        :param test_name: Mandatory, Pytest node id.
        :return: Trace zip path.
        """
        return self.test_dir(test_name).joinpath(f"{self._timestamp()}_trace.zip")

    def _timestamp(self) -> str:
        """
        Get a timestamp for artifact file names.

        :return: Timestamp string.
        """
        now_value = datetime.now(UTC) if self.timezone_name == "UTC" else datetime.now()
        return now_value.strftime("%Y%m%d_%H%M%S")


def sanitize_test_name(test_name: str) -> str:
    """
    Replace characters that are unsafe in file names.

    :param test_name: Mandatory, Test name to sanitize.
    :return: Safe file system name.
    """
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in test_name)
