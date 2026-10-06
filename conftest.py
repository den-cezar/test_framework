"""
Root pytest hooks. Must not require an env file, so unit tests run without one.
End-to-end fixtures live in test_scripts/conftest.py.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from core.reporting.summary import OUTCOMES, RunSummary, render_markdown

RUN_STARTED_AT_ENV = "TEST_RUN_STARTED_AT"


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Register custom command-line options for the framework.

    :param parser: Mandatory, Pytest CLI parser.
    """
    parser.addoption("--env-file", action="store", default=None, help="Path to .env file for the framework.")


def pytest_configure(config: pytest.Config) -> None:
    """
    Record the run start time on the controller; xdist workers inherit it through the environment.

    :param config: Mandatory, Pytest config.
    """
    if not hasattr(config, "workerinput"):
        os.environ[RUN_STARTED_AT_ENV] = str(time.time())


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter, config: pytest.Config) -> None:
    """
    Append a Markdown result table to the GitHub Actions job summary when running in CI.

    :param terminalreporter: Mandatory, Pytest terminal reporter.
    :param config: Mandatory, Pytest config.
    """
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path or hasattr(config, "workerinput"):
        return

    stats = terminalreporter.stats
    failures = [
        (report.nodeid or "collection", _failure_message(report))
        for outcome in ("failed", "error")
        for report in stats.get(outcome, [])
    ]
    summary = RunSummary(
        title=os.getenv("TEST_SUMMARY_TITLE", "Test results"),
        counts={outcome: len(stats.get(outcome, [])) for outcome in OUTCOMES},
        failures=failures,
        duration_seconds=time.time() - float(os.environ[RUN_STARTED_AT_ENV]),
    )
    with Path(summary_path).open("a", encoding="utf-8") as summary_file:
        summary_file.write(render_markdown(summary))


def _failure_message(report: pytest.TestReport | pytest.CollectReport) -> str:
    """
    Extract the one-line crash message from a failed report.

    :param report: Mandatory, Failed test or collection report.
    :return: Crash message.
    """
    crash = getattr(report.longrepr, "reprcrash", None)
    if crash is not None:
        return str(crash.message)
    lines = str(report.longrepr).strip().splitlines()
    return lines[-1] if lines else ""
