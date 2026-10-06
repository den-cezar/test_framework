from pathlib import Path

from tools.mutation_score import mutation_score
from tools.mutation_score import render as render_mutation
from tools.report_history import RunEntry, parse_junit, render_index, update_history

JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="1" failures="2" skipped="3" tests="10" time="4.5"/></testsuites>"""


def _entry(run_number: int, browser: str = "chromium", failed: int = 0) -> RunEntry:
    return RunEntry(
        run_number=run_number,
        browser=browser,
        suite="regression",
        date="2026-10-06 10:00",
        total=10,
        passed=10 - failed,
        failed=failed,
        skipped=0,
        duration_seconds=1.0,
        run_url=f"https://example.test/runs/{run_number}",
        report_path=f"runs/{run_number}-{browser}/report.html",
    )


def test_parse_junit_sums_failures_and_errors(tmp_path: Path) -> None:
    path = tmp_path.joinpath("junit.xml")
    path.write_text(JUNIT, encoding="utf-8")

    assert parse_junit(path) == (10, 3, 3, 4.5)


def test_history_is_newest_first_deduplicated_and_trimmed() -> None:
    history = [_entry(1), _entry(2), _entry(2, "firefox")]

    kept, dropped = update_history(history, _entry(2, failed=1), keep=2)

    assert [entry.key for entry in kept] == ["2-firefox", "2-chromium"]
    assert kept[1].failed == 1
    assert [entry.key for entry in dropped] == ["1-chromium"]


def test_pass_rate_ignores_skipped() -> None:
    entry = RunEntry(
        1,
        "webkit",
        "smoke",
        "d",
        total=4,
        passed=2,
        failed=1,
        skipped=1,
        duration_seconds=0,
        run_url="",
        report_path="",
    )

    assert round(entry.pass_rate) == 67


def test_index_escapes_values_and_marks_failures() -> None:
    page = render_index([_entry(3, browser="<b>", failed=1), _entry(2)], "owner/repo")

    assert "&lt;b&gt;" in page and "<b>" not in page.split("<body>")[1]
    assert page.count("FAILED") == 1
    assert 'href="runs/2-chromium/report.html"' in page


def test_mutation_score_counts_timeouts_and_excludes_skipped() -> None:
    stats = {"killed": 70, "timeout": 10, "survived": 20, "skipped": 10, "total": 110, "no_tests": 0, "suspicious": 0}

    assert mutation_score(stats) == 80.0
    assert "FAILED" in render_mutation(stats, 80.0, min_score=85)
    assert "PASSED" in render_mutation(stats, 80.0, min_score=80)
