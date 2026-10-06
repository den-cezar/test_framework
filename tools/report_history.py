"""
Maintain a history of e2e runs on the gh-pages branch: copy the run's HTML report and rebuild index.html.

Usage:
  python -m tools.report_history --site site --junit reports/junit.xml --report reports/report.html \
      --run-number 12 --run-url https://... --suite regression --browser chromium
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path

KEEP_RUNS = 50
CHART_RUNS = 30


@dataclass(frozen=True)
class RunEntry:
    """One e2e run in the history."""

    run_number: int
    browser: str
    suite: str
    date: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    run_url: str
    report_path: str

    @property
    def key(self) -> str:
        """Unique key; a matrix run produces one entry per browser."""
        return f"{self.run_number}-{self.browser}"

    @property
    def pass_rate(self) -> float:
        """Passed share of executed (non-skipped) tests, in percent."""
        executed = self.total - self.skipped
        return 100.0 * self.passed / executed if executed else 100.0


def parse_junit(junit_path: Path) -> tuple[int, int, int, float]:
    """
    Sum counts over all test suites in a JUnit XML file.

    :param junit_path: Mandatory, JUnit XML path.
    :return: total, failed (failures + errors), skipped, duration in seconds.
    """
    root = ET.parse(junit_path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = sum(int(suite.get("tests", 0)) for suite in suites)
    failed = sum(int(suite.get("failures", 0)) + int(suite.get("errors", 0)) for suite in suites)
    skipped = sum(int(suite.get("skipped", 0)) for suite in suites)
    duration = sum(float(suite.get("time", 0)) for suite in suites)
    return total, failed, skipped, duration


def update_history(
    history: list[RunEntry], entry: RunEntry, keep: int = KEEP_RUNS
) -> tuple[list[RunEntry], list[RunEntry]]:
    """
    Add or replace an entry and keep the newest runs.

    :param history: Mandatory, Existing entries.
    :param entry: Mandatory, New entry.
    :param keep: Optional, Number of entries to keep.
    :return: Kept entries (newest first) and dropped entries.
    """
    merged = [item for item in history if item.key != entry.key] + [entry]
    merged.sort(key=lambda item: (item.run_number, item.browser), reverse=True)
    return merged[:keep], merged[keep:]


def render_index(history: list[RunEntry], repository: str) -> str:
    """
    Render the history page.

    :param history: Mandatory, Entries, newest first.
    :param repository: Mandatory, owner/repo, used in the title.
    :return: HTML document.
    """
    chart = list(reversed(history[:CHART_RUNS]))
    bar_width = 18
    bars = "".join(
        f'<rect x="{index * (bar_width + 4)}" y="{100 - entry.pass_rate:.1f}" width="{bar_width}" '
        f'height="{entry.pass_rate:.1f}" class="{"ok" if entry.failed == 0 else "bad"}">'
        f"<title>#{entry.run_number} {escape(entry.browser)}: {entry.pass_rate:.0f}% passed</title></rect>"
        for index, entry in enumerate(chart)
    )
    rows = "".join(
        "<tr>"
        f'<td><a href="{escape(entry.run_url)}">#{entry.run_number}</a></td>'
        f"<td>{escape(entry.date)}</td><td>{escape(entry.suite)}</td><td>{escape(entry.browser)}</td>"
        f'<td class="{"ok" if entry.failed == 0 else "bad"}">{"PASSED" if entry.failed == 0 else "FAILED"}</td>'
        f"<td>{entry.passed}/{entry.total - entry.skipped}</td><td>{entry.failed}</td><td>{entry.skipped}</td>"
        f"<td>{entry.duration_seconds:.1f}s</td>"
        f'<td><a href="{escape(entry.report_path)}">report</a></td>'
        "</tr>"
        for entry in history
    )
    width = max(len(chart), 1) * (bar_width + 4)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>E2E history: {escape(repository)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; background: #fff; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border-bottom: 1px solid #d0d0d0; padding: .4rem .6rem; text-align: left; }}
  th {{ background: #f2f2f2; }}
  .ok {{ color: #0a6b2d; fill: #1f8f45; }}
  .bad {{ color: #b00020; fill: #c62828; }}
  svg {{ border-left: 1px solid #888; border-bottom: 1px solid #888; margin-bottom: 1.5rem; }}
</style>
</head>
<body>
<main>
<h1>E2E test history</h1>
<p>{escape(repository)}: last {len(history)} runs. Pass rate of the last {len(chart)} runs, oldest on the left:</p>
<svg role="img" aria-label="Pass rate per run" width="{width}" height="100" viewBox="0 0 {width} 100">{bars}</svg>
<table>
<thead><tr><th>Run</th><th>Date (UTC)</th><th>Suite</th><th>Browser</th><th>Result</th>
<th>Passed</th><th>Failed</th><th>Skipped</th><th>Duration</th><th>Report</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</main>
</body>
</html>
"""


def main() -> int:
    """
    Entry point.

    :return: Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--run-number", type=int, required=True)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--browser", required=True)
    parser.add_argument("--repository", default="")
    args = parser.parse_args()

    total, failed, skipped, duration = parse_junit(args.junit)
    report_rel = f"runs/{args.run_number}-{args.browser}/report.html"
    report_target = args.site.joinpath(report_rel)
    report_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.report, report_target)

    entry = RunEntry(
        run_number=args.run_number,
        browser=args.browser,
        suite=args.suite,
        date=datetime.now(UTC).strftime("%Y-%m-%d %H:%M"),
        total=total,
        passed=total - failed - skipped,
        failed=failed,
        skipped=skipped,
        duration_seconds=duration,
        run_url=args.run_url,
        report_path=report_rel,
    )
    history_file = args.site.joinpath("history.json")
    existing = (
        [RunEntry(**item) for item in json.loads(history_file.read_text(encoding="utf-8"))]
        if history_file.exists()
        else []
    )
    kept, dropped = update_history(existing, entry)
    for old in dropped:
        shutil.rmtree(args.site.joinpath(old.report_path).parent, ignore_errors=True)

    history_file.write_text(json.dumps([asdict(item) for item in kept], indent=2), encoding="utf-8")
    args.site.joinpath("index.html").write_text(render_index(kept, args.repository), encoding="utf-8")
    args.site.joinpath(".nojekyll").touch()
    print(f"History updated: {entry.key} ({entry.passed}/{entry.total - entry.skipped} passed), {len(kept)} runs kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
