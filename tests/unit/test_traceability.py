from core.reporting.traceability import NOT_IN_CATALOG, build_matrix, render_traceability_markdown

CATALOG = {"REQ-1": "First", "REQ-2": "Second", "REQ-3": "Third", "REQ-4": "Fourth"}


def test_status_per_requirement() -> None:
    rows = build_matrix(
        CATALOG,
        [
            ("REQ-1", "t.py::a", "passed"),
            ("REQ-1", "t.py::b[x]", "passed"),
            ("REQ-2", "t.py::c", "passed"),
            ("REQ-2", "t.py::d", "failed"),
            ("REQ-3", "t.py::e", "skipped"),
        ],
    )

    assert [(row.scenario_id, row.tests, row.status) for row in rows] == [
        ("REQ-1", 2, "PASSED"),
        ("REQ-2", 2, "FAILED"),
        ("REQ-3", 1, "SKIPPED"),
        ("REQ-4", 0, "NOT RUN"),
    ]


def test_setup_error_counts_as_failure() -> None:
    rows = build_matrix({"REQ-1": "x"}, [("REQ-1", "t.py::a", "error")])

    assert rows[0].status == "FAILED"


def test_unknown_scenario_is_listed_after_catalog() -> None:
    rows = build_matrix({"REQ-1": "x"}, [("ZZZ-9", "t.py::a", "passed")])

    assert rows[-1].scenario_id == "ZZZ-9"
    assert rows[-1].title == NOT_IN_CATALOG


def test_render_counts_and_escapes() -> None:
    rows = build_matrix({"REQ-1": "a | b", "REQ-2": "c"}, [("REQ-1", "t.py::a", "failed")])

    markdown = render_traceability_markdown(rows)

    assert markdown == "\n".join(
        [
            "#### Requirements traceability: 1/2 executed, 1 failed",
            "",
            "| Requirement | Description | Tests | Status |",
            "|---|---|---|---|",
            "| `REQ-1` | a \\| b | 1 | FAILED |",
            "| `REQ-2` | c | 0 | NOT RUN |",
            "",
        ]
    )
