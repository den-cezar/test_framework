"""Utility helpers for loading structured data files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(file_path: Path) -> dict[str, Any]:
    """
    Load JSON data from a file path.

    :param file_path: Mandatory, Path to a JSON file.
    :return: Parsed JSON content.
    """
    if not isinstance(file_path, Path):
        raise ValueError("file_path must be a Path.")
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"JSON file is empty: {file_path}")

    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")
    return data
