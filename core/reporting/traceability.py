"""
Requirements traceability: map scenario ids to test results.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from core.reporting.summary import escape_cell

FAILED_OUTCOMES = frozenset({"failed", "error"})
PASSED_OUTCOMES = frozenset({"passed"})
NOT_IN_CATALOG = "(not in requirements catalog)"


@dataclass(frozen=True)
class TraceRow:
    """Result of one requirement in a run."""

    scenario_id: str
    title: str
    tests: int
    status: str


def build_matrix(catalog: Mapping[str, str], results: Iterable[tuple[str, str, str]]) -> list[TraceRow]:
    """
    Combine the requirements catalog with test results.

    :param catalog: Mandatory, Scenario id to requirement title.
    :param results: Mandatory, (scenario id, test node id, outcome) per test report.
    :return: One row per requirement, catalog order first, then unknown ids.
    """
    outcomes: dict[str, set[str]] = defaultdict(set)
    tests: dict[str, set[str]] = defaultdict(set)
    for scenario_id, node_id, outcome in results:
        outcomes[scenario_id].add(outcome)
        tests[scenario_id].add(node_id)

    ordered_ids = list(catalog) + sorted(outcomes.keys() - catalog.keys())
    return [
        TraceRow(
            scenario_id=scenario_id,
            title=catalog.get(scenario_id, NOT_IN_CATALOG),
            tests=len(tests[scenario_id]),
            status=_status(outcomes[scenario_id]),
        )
        for scenario_id in ordered_ids
    ]


def render_traceability_markdown(rows: Iterable[TraceRow]) -> str:
    """
    Render the traceability matrix as Markdown.

    :param rows: Mandatory, Matrix rows.
    :return: Markdown text.
    """
    rows = list(rows)
    executed = sum(row.status != "NOT RUN" for row in rows)
    failed = sum(row.status == "FAILED" for row in rows)
    lines = [
        f"#### Requirements traceability: {executed}/{len(rows)} executed, {failed} failed",
        "",
        "| Requirement | Description | Tests | Status |",
        "|---|---|---|---|",
        *(
            f"| `{escape_cell(row.scenario_id)}` | {escape_cell(row.title)} | {row.tests} | {row.status} |"
            for row in rows
        ),
        "",
    ]
    return "\n".join(lines)


def _status(outcomes: set[str]) -> str:
    """
    Collapse test outcomes into a requirement status.

    :param outcomes: Mandatory, Outcomes of all tests for one requirement.
    :return: FAILED, PASSED, SKIPPED or NOT RUN.
    """
    if outcomes & FAILED_OUTCOMES:
        return "FAILED"
    if outcomes & PASSED_OUTCOMES:
        return "PASSED"
    if outcomes:
        return "SKIPPED"
    return "NOT RUN"
