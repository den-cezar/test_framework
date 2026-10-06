import logging
from pathlib import Path

import pytest

from core.artifacts.artifact_manager import ArtifactManager, sanitize_test_name
from core.logging.logger import Logger


class FakePage:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def screenshot(self, *, path: str | Path | None = None) -> bytes:
        assert path is not None
        Path(path).write_bytes(b"png")
        self.paths.append(Path(path))
        return b"png"


def test_sanitize_test_name() -> None:
    assert sanitize_test_name("tests/ui/test_x.py::test_y[a b]") == "tests_ui_test_x.py__test_y_a_b_"


def test_screenshot_and_trace_go_to_the_test_directory(tmp_path: Path) -> None:
    manager = ArtifactManager(tmp_path.joinpath("not", "created", "yet"), "UTC")
    page = FakePage()

    path, png = manager.capture_screenshot(page, "suite/test_a.py::test_b")
    trace = manager.trace_path("suite/test_a.py::test_b")

    assert png == b"png"
    assert path.read_bytes() == b"png"
    assert path.parent == trace.parent == tmp_path.joinpath("not", "created", "yet", "suite_test_a.py__test_b")
    assert trace.parent.is_dir()
    assert path.name.endswith("_error_screenshot.png")
    assert trace.name.endswith("_trace.zip")


def test_artifact_manager_rejects_unknown_timezone(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="UTC or LOCAL"):
        ArtifactManager(tmp_path, "CET")


def test_logger_writes_worker_file_with_test_name(tmp_path: Path) -> None:
    instance = Logger.get_instance("gw7", tmp_path, console_level="ERROR", file_level="INFO")
    try:
        assert Logger.get_instance("gw7", tmp_path) is instance
        instance.set_test_name("tests/unit::test_logger")
        Logger.get_logger("Unit").info("hello")
        Logger.get_logger("Unit").debug("below file level")
    finally:
        instance.cleanup()

    content = tmp_path.joinpath("gw7.log").read_text(encoding="utf-8")
    assert "[gw7] - tests/unit::test_logger - INFO - test_framework.Unit - hello" in content
    assert "below file level" not in content
    assert logging.getLogger("test_framework").handlers == []
