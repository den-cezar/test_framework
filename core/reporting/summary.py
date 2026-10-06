"""
Reporting helpers that turn a pytest session into a GitHub job summary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

OUTCOMES = ("passed", "failed", "error", "skipped", "xfailed", "xpassed")
MAX_LISTED_FAILURES = 50
MAX_MESSAGE_CHARS = 300


@dataclass(frozen=True)
class RunSummary:
    """
    Aggregated outcome of a test session.
    """

    title: str
    counts: Mapping[str, int]
    failures: Sequence[tuple[str, str]]
    duration_seconds: float

    @property
    def total(self) -> int:
        """Number of tests across all outcomes."""
        return sum(self.counts.get(outcome, 0) for outcome in OUTCOMES)

    @property
    def succeeded(self) -> bool:
        """True when nothing failed or errored."""
        return not (self.counts.get("failed", 0) or self.counts.get("error", 0))


def render_markdown(summary: RunSummary) -> str:
    """
    Render a run summary as GitHub-flavoured Markdown.

    :param summary: Mandatory, Aggregated run outcome.
    :return: Markdown text.
    """
    status = "PASSED" if summary.succeeded else "FAILED"
    lines = [
        f"### {_escape(summary.title)}: {status}",
        "",
        "| Total | " + " | ".join(outcome.capitalize() for outcome in OUTCOMES) + " | Duration |",
        "|---" * (len(OUTCOMES) + 2) + "|",
        f"| {summary.total} | "
        + " | ".join(str(summary.counts.get(outcome, 0)) for outcome in OUTCOMES)
        + f" | {summary.duration_seconds:.1f}s |",
        "",
    ]

    if summary.failures:
        shown = summary.failures[:MAX_LISTED_FAILURES]
        lines += [
            f"<details open><summary>Failures ({len(summary.failures)})</summary>",
            "",
            "| Test | Error |",
            "|---|---|",
            *(f"| `{_escape(node_id)}` | {_escape(message)} |" for node_id, message in shown),
            "",
        ]
        if len(summary.failures) > len(shown):
            lines += [f"_{len(summary.failures) - len(shown)} more not shown; see the HTML report._", ""]
        lines += ["</details>", ""]

    return "\n".join(lines)


def _escape(text: str) -> str:
    """
    Make text safe for a single Markdown table cell.

    :param text: Mandatory, Raw text.
    :return: Escaped, single-line, truncated text.
    """
    single_line = " ".join(text.split())
    if len(single_line) > MAX_MESSAGE_CHARS:
        single_line = single_line[: MAX_MESSAGE_CHARS - 3] + "..."
    return single_line.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
