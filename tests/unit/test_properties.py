"""
Property-based tests: invariants that must hold for any input, not just hand-picked examples.
"""

import re
import string
import time

from hypothesis import given
from hypothesis import strategies as st

from core.artifacts.artifact_manager import sanitize_test_name
from core.auth.token_cache import TokenRecord
from core.config.settings import parse_launch_args
from core.reporting.summary import MAX_MESSAGE_CHARS, escape_cell
from core.reporting.traceability import build_matrix

SAFE_FILE_CHARS = set(string.ascii_letters + string.digits + "-_.")
OUTCOMES = st.sampled_from(["passed", "failed", "error", "skipped", "xfailed"])


@given(st.text(alphabet=st.characters(codec="ascii")))
def test_sanitized_names_are_safe_same_length_and_stable(name: str) -> None:
    sanitized = sanitize_test_name(name)

    assert set(sanitized) <= SAFE_FILE_CHARS
    assert len(sanitized) == len(name)
    assert sanitize_test_name(sanitized) == sanitized


@given(st.text())
def test_escaped_cells_cannot_break_a_markdown_table(text: str) -> None:
    cell = escape_cell(text)

    assert "\n" not in cell and "\r" not in cell
    assert not re.search(r"(?<!\\)\|", cell), "unescaped pipe"
    assert "<" not in cell and ">" not in cell
    assert len(cell.replace("\\|", "|").replace("&lt;", "<").replace("&gt;", ">")) <= MAX_MESSAGE_CHARS


@given(st.text(alphabet=string.ascii_letters + string.digits + " -_", max_size=200))
def test_plain_short_text_only_has_whitespace_normalised(text: str) -> None:
    assert escape_cell(text) == " ".join(text.split())


@given(st.lists(st.text(alphabet=string.ascii_letters + "-=_", min_size=1), max_size=8))
def test_launch_args_round_trip(args: list[str]) -> None:
    assert parse_launch_args(" , ".join(args)) == tuple(args)


@given(st.integers(min_value=0, max_value=3600), st.integers(min_value=0, max_value=3600))
def test_larger_refresh_skew_never_makes_a_token_less_expired(skew_a: int, skew_b: int) -> None:
    record = TokenRecord(access_token="t", expires_at=time.time() + 1800)
    low, high = sorted((skew_a, skew_b))

    assert record.is_expired(high) or not record.is_expired(low)


@given(st.lists(st.tuples(st.sampled_from(["R1", "R2", "R3"]), st.sampled_from(["a", "b", "c"]), OUTCOMES)))
def test_requirement_fails_exactly_when_one_of_its_tests_fails(results: list[tuple[str, str, str]]) -> None:
    rows = {row.scenario_id: row for row in build_matrix({"R1": "", "R2": "", "R3": ""}, results)}

    for scenario_id, row in rows.items():
        outcomes = {outcome for sid, _, outcome in results if sid == scenario_id}
        assert (row.status == "FAILED") == bool(outcomes & {"failed", "error"})
        assert row.tests == len({node for sid, node, _ in results if sid == scenario_id})
        assert (row.status == "NOT RUN") == (not outcomes)
