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
