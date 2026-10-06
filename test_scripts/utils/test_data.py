"""Helpers for loading test data files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils.data_loader import load_json

DATA_ROOT = Path(__file__).resolve().parents[1].joinpath("data")


def load_test_data() -> dict[str, Any]:
    """
    Load the shared test data JSON.

    :return: Test data mapping.
    """
    return load_json(DATA_ROOT.joinpath("test_data.json"))


def load_json_file(file_name: str) -> dict[str, Any]:
    """
    Load a JSON file from test_scripts/data.

    :param file_name: Mandatory, File name inside the data folder.
    :return: Parsed mapping.
    """
    return load_json(DATA_ROOT.joinpath(file_name))
