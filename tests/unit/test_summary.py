from core.reporting.summary import MAX_LISTED_FAILURES, RunSummary, render_markdown


def test_passing_run() -> None:
    markdown = render_markdown(
        RunSummary(title="Unit tests", counts={"passed": 3, "skipped": 1}, failures=[], duration_seconds=1.234)
    )

    assert markdown.startswith("### Unit tests: PASSED")
    assert "| 4 | 3 | 0 | 0 | 1 | 0 | 0 | 1.2s |" in markdown
    assert "Failures" not in markdown
    assert "rerun" not in markdown


def test_exact_markdown_layout() -> None:
    markdown = render_markdown(
        RunSummary(title="T", counts={"passed": 1, "failed": 1}, failures=[("a.py::t", "boom")], duration_seconds=2)
    )

    assert markdown == "\n".join(
        [
            "### T: FAILED",
            "",
            "| Total | Passed | Failed | Error | Skipped | Xfailed | Xpassed | Duration |",
            "|---|---|---|---|---|---|---|---|",
            "| 2 | 1 | 1 | 0 | 0 | 0 | 0 | 2.0s |",
            "",
            "<details open><summary>Failures (1)</summary>",
            "",
            "| Test | Error |",
            "|---|---|",
            "| `a.py::t` | boom |",
            "",
            "</details>",
            "",
        ]
    )


def test_flaky_tests_are_listed() -> None:
    markdown = render_markdown(
        RunSummary(
            title="E2E", counts={"passed": 2}, failures=[], duration_seconds=1, flaky=["t.py::test_a", "t.py::test_b"]
        )
    )

    assert markdown.startswith("### E2E: PASSED")
    assert "Passed only after a rerun (2)" in markdown
    assert "- `t.py::test_b`" in markdown


def test_failures_are_listed_and_escaped() -> None:
    markdown = render_markdown(
        RunSummary(
            title="E2E",
            counts={"passed": 1, "failed": 1, "error": 1},
            failures=[("t.py::test_a", "assert 'a|b'\n == <c>"), ("t.py::test_b", "boom")],
            duration_seconds=2,
        )
    )

    assert markdown.startswith("### E2E: FAILED")
    assert "Failures (2)" in markdown
    assert "| `t.py::test_a` | assert 'a\\|b' == &lt;c&gt; |" in markdown


def test_long_failure_lists_are_truncated() -> None:
    failures = [(f"t.py::test_{index}", "x" * 1000) for index in range(MAX_LISTED_FAILURES + 5)]

    markdown = render_markdown(
        RunSummary(title="E2E", counts={"failed": len(failures)}, failures=failures, duration_seconds=0)
    )

    assert markdown.count("| `t.py::test_") == MAX_LISTED_FAILURES
    assert "_5 more not shown; see the HTML report._" in markdown
    assert "x" * 400 not in markdown
