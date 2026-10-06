"""
Root pytest hooks. Must not require an env file, so unit tests run without one.
End-to-end fixtures live in test_scripts/conftest.py.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from core.reporting.summary import OUTCOMES, RunSummary, render_markdown
from core.reporting.traceability import build_matrix, render_traceability_markdown

RUN_STARTED_AT_ENV = "TEST_RUN_STARTED_AT"


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Register custom command-line options for the framework.

    :param parser: Mandatory, Pytest CLI parser.
    """
    parser.addoption("--env-file", action="store", default=None, help="Path to .env file for the framework.")
    parser.addoption(
        "--require-full-traceability",
        action="store_true",
        help="Fail collection if any requirement in the catalog has no test.",
    )
    parser.addoption(
        "--traceability-report", action="store", default=None, help="Write the traceability matrix (Markdown) here."
    )
    parser.addini("requirements_catalog", "JSON file mapping scenario ids to requirement titles.", default="")


def pytest_configure(config: pytest.Config) -> None:
    """
    Record the run start time on the controller; xdist workers inherit it through the environment.

    :param config: Mandatory, Pytest config.
    """
    if not hasattr(config, "workerinput"):
        os.environ[RUN_STARTED_AT_ENV] = str(time.time())


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter, config: pytest.Config) -> None:
    """
    Write the job summary (in GitHub Actions) and the traceability matrix (when requested or in CI).

    :param terminalreporter: Mandatory, Pytest terminal reporter.
    :param config: Mandatory, Pytest config.
    """
    if hasattr(config, "workerinput"):
        return
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    traceability_path = config.getoption("--traceability-report")
    stats = terminalreporter.stats
    sections: list[str] = []

    if summary_path:
        rerun_ids = {report.nodeid for report in stats.get("rerun", [])}
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
            flaky=sorted(report.nodeid for report in stats.get("passed", []) if report.nodeid in rerun_ids),
        )
        sections.append(render_markdown(summary))

    traceability = _traceability_markdown(config, stats)
    if traceability and traceability_path:
        Path(traceability_path).parent.mkdir(parents=True, exist_ok=True)
        Path(traceability_path).write_text(traceability, encoding="utf-8")
    if traceability and summary_path:
        sections.append(traceability)

    if summary_path and sections:
        with Path(summary_path).open("a", encoding="utf-8") as summary_file:
            summary_file.write("\n".join(sections))


def _traceability_markdown(config: pytest.Config, stats: dict[str, list[pytest.TestReport]]) -> str:
    """
    Build the traceability matrix if a catalog is configured and any test carried a scenario id.

    :param config: Mandatory, Pytest config.
    :param stats: Mandatory, Terminal reporter stats.
    :return: Markdown, or an empty string when not applicable.
    """
    catalog_setting = str(config.getini("requirements_catalog"))
    results = [
        (str(value), report.nodeid, outcome)
        for outcome in OUTCOMES
        for report in stats.get(outcome, [])
        for name, value in getattr(report, "user_properties", [])
        if name == "scenario"
    ]
    if not catalog_setting or not results:
        return ""
    catalog = json.loads(config.rootpath.joinpath(catalog_setting).read_text(encoding="utf-8"))
    return render_traceability_markdown(build_matrix(catalog, results))


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
