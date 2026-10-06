from pathlib import Path

import pytest

from core.utils.data_loader import load_json


def test_loads_json_object(tmp_path: Path) -> None:
    path = tmp_path.joinpath("data.json")
    path.write_text('{"a": [1, 2]}', encoding="utf-8")

    assert load_json(path) == {"a": [1, 2]}


@pytest.mark.parametrize(
    ("content", "error", "message"),
    [
        (None, FileNotFoundError, "not found"),
        ("  ", ValueError, "empty"),
        ("[1, 2]", ValueError, "root must be an object"),
    ],
)
def test_rejects_invalid_files(tmp_path: Path, content: str | None, error: type[Exception], message: str) -> None:
    path = tmp_path.joinpath("data.json")
    if content is not None:
        path.write_text(content, encoding="utf-8")

    with pytest.raises(error, match=message):
        load_json(path)
