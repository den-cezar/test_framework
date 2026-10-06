"""
Accessibility scans with axe-core. Known third-party violations are baselined so only new ones fail.
"""

import warnings

import pytest

from domain.ui.ui_service import UiService
from test_scripts.utils.test_data import load_json_file

BASELINE: dict[str, list[str]] = load_json_file("a11y_baseline.json")["known_violations"]

pytestmark = [pytest.mark.ui, pytest.mark.a11y, pytest.mark.regression]


def _assert_no_new_violations(ui_service: UiService, page_key: str) -> None:
    """Fail on serious/critical rules missing from the baseline; warn when a baselined rule is gone."""
    found = {violation.rule_id: violation for violation in ui_service.accessibility_violations("serious")}
    known = set(BASELINE.get(page_key, []))

    new = {rule: found[rule] for rule in found.keys() - known}
    assert not new, "New accessibility violations:\n" + "\n".join(
        f"- {v.rule_id} ({v.impact}, {v.nodes} nodes): {v.help}" for v in new.values()
    )
    if fixed := known - found.keys():
        warnings.warn(f"{page_key}: baselined rules no longer reported, remove them: {sorted(fixed)}", stacklevel=2)


@pytest.mark.scenario("UI-A11Y-0001")
def test_todo_app_has_no_new_accessibility_violations(ui_service: UiService) -> None:
    """Scan with items present, so list markup is included."""
    ui_service.open_todo_app(seeded_items=["Scan me"])

    _assert_no_new_violations(ui_service, "todomvc")


@pytest.mark.scenario("UI-A11Y-0002")
def test_fruit_list_has_no_new_accessibility_violations(ui_service: UiService) -> None:
    """Scan after the list has rendered."""
    page = ui_service.fruits_page().open()
    page.items.first.wait_for()

    _assert_no_new_violations(ui_service, "api-mocking")
