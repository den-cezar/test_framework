"""
Shared helpers for framework unit tests. No network, no env file.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from core.config.settings import FrameworkSettings, OAuthClientConfig

BASE_ENV = {
    "ENV_NAME": "unit",
    "API_BASE_URL": "https://api.example.test",
    "UI_BASE_URL": "https://ui.example.test",
    "OAUTH_TOKEN_URL": "https://idp.example.test/connect/token",
    "OAUTH_CLIENT_NAME_A": "client_a",
    "OAUTH_CLIENT_ID_A": "id-a",
    "OAUTH_CLIENT_SECRET_A": "secret-a",
    "OAUTH_SCOPE_A": "api",
    "TOKEN_CACHE_PATH": ".cache/token_cache.json",
    "LOG_CONSOLE_LEVEL": "INFO",
    "LOG_FILE_LEVEL": "DEBUG",
    "TIMEZONE": "UTC",
}


@pytest.fixture
def write_env(tmp_path: Path) -> Callable[..., Path]:
    """
    Return a function that writes BASE_ENV plus overrides to an env file. Pass None to drop a key.

    :param tmp_path: Mandatory, Pytest temp dir.
    :return: Env file writer.
    """

    def _write(**overrides: str | None) -> Path:
        values = {**BASE_ENV, **overrides}
        env_file = tmp_path.joinpath(".env.unit")
        env_file.write_text(
            "\n".join(f"{key}={value}" for key, value in values.items() if value is not None), encoding="utf-8"
        )
        return env_file

    return _write


@pytest.fixture
def settings(tmp_path: Path) -> FrameworkSettings:
    """
    Settings with one OAuth client, built without an env file.

    :param tmp_path: Mandatory, Pytest temp dir.
    :return: FrameworkSettings instance.
    """
    return FrameworkSettings(
        env_name="unit",
        api_base_url="https://api.example.test",
        ui_base_url="https://ui.example.test",
        oauth_token_url="https://idp.example.test/connect/token",
        oauth_client_name=None,
        oauth_clients={"client_a": OAuthClientConfig(client_id="id-a", client_secret="secret-a", scope="api")},
        token_cache_path=tmp_path.joinpath("token_cache.json"),
        log_console_level="INFO",
        log_file_level="DEBUG",
        timezone="UTC",
    )
