from collections.abc import Callable
from pathlib import Path

import pytest

from core.config.settings import OAuthClientConfig, load_settings, parse_launch_args, resolve_env_file
from core.errors import ConfigError
from tests.unit.conftest import BASE_ENV


def test_loads_valid_env_file(write_env: Callable[..., Path]) -> None:
    settings = load_settings(write_env(), environ={})

    assert settings.env_name == "unit"
    assert settings.ui_base_url == "https://ui.example.test"
    assert settings.oauth_clients["client_a"].client_id == "id-a"
    assert settings.oauth_clients["client_a"].scope == "api"
    assert settings.http_timeout_seconds == 30
    assert settings.playwright_headless is True
    assert settings.playwright_launch_args == ()


def test_optional_values_are_parsed(write_env: Callable[..., Path]) -> None:
    settings = load_settings(
        write_env(
            HTTP_TIMEOUT_SECONDS="5.5",
            PLAYWRIGHT_HEADLESS="false",
            PLAYWRIGHT_LAUNCH_ARGS="--no-sandbox, ,--disable-gpu",
            PLAYWRIGHT_BROWSER=" Firefox ",
            LOG_CONSOLE_LEVEL="warning",
        ),
        environ={},
    )

    assert settings.http_timeout_seconds == 5.5
    assert settings.playwright_headless is False
    assert settings.playwright_launch_args == ("--no-sandbox", "--disable-gpu")
    assert settings.playwright_browser == "firefox"
    assert settings.log_console_level == "WARNING"


def test_legacy_and_default_clients_are_loaded(write_env: Callable[..., Path]) -> None:
    settings = load_settings(
        write_env(
            OAUTH_CLIENT_ID="default-id",
            OAUTH_CLIENT_SECRET="default-secret",
            OAUTH_CLIENT_ID_LEGACY="legacy-id",
            OAUTH_CLIENT_SECRET_LEGACY="legacy-secret",
            OAUTH_CLIENT_NAME="legacy",
        ),
        environ={},
    )

    assert set(settings.oauth_clients) == {"default", "client_a", "legacy"}
    assert settings.resolve_oauth_client() == ("legacy", settings.oauth_clients["legacy"])


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"UI_BASE_URL": None}, "UI_BASE_URL"),
        ({"OAUTH_CLIENT_SECRET_A": None}, "OAUTH_CLIENT_SECRET_A"),
        ({"OAUTH_CLIENT_NAME_A": None, "OAUTH_CLIENT_ID_A": None}, "At least one OAuth client"),
        ({"OAUTH_CLIENT_NAME": "missing"}, "not found: missing"),
        ({"TIMEZONE": "CET"}, "TIMEZONE"),
        ({"LOG_FILE_LEVEL": "LOUD"}, "LOG_FILE_LEVEL"),
        ({"HTTP_TIMEOUT_SECONDS": "soon"}, "HTTP_TIMEOUT_SECONDS"),
        ({"HTTP_TIMEOUT_SECONDS": "0"}, "HTTP_TIMEOUT_SECONDS"),
        ({"PLAYWRIGHT_HEADLESS": "maybe"}, "PLAYWRIGHT_HEADLESS"),
        ({"PLAYWRIGHT_BROWSER": "edge"}, "PLAYWRIGHT_BROWSER"),
        ({"OAUTH_CLIENT_NAME_B": "CLIENT_A", "OAUTH_CLIENT_ID_B": "x", "OAUTH_CLIENT_SECRET_B": "y"}, "Duplicate"),
    ],
)
def test_invalid_config_raises_config_error(
    write_env: Callable[..., Path], overrides: dict[str, str | None], message: str
) -> None:
    with pytest.raises(ConfigError, match=message):
        load_settings(write_env(**overrides), environ={})


def test_missing_env_file_raises_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Env file not found"):
        load_settings(tmp_path.joinpath("absent.env"), environ={})


def test_environment_overrides_file_values(write_env: Callable[..., Path]) -> None:
    settings = load_settings(
        write_env(), environ={"API_BASE_URL": "https://ci.example.test", "OAUTH_CLIENT_SECRET_A": "from-secret"}
    )

    assert settings.api_base_url == "https://ci.example.test"
    assert settings.oauth_clients["client_a"].client_secret == "from-secret"


def test_process_environment_is_used_by_default(
    write_env: Callable[..., Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UI_BASE_URL", "https://from-process.example.test")

    assert load_settings(write_env()).ui_base_url == "https://from-process.example.test"


def test_default_client_keeps_its_scope(write_env: Callable[..., Path]) -> None:
    settings = load_settings(
        write_env(OAUTH_CLIENT_ID="d-id", OAUTH_CLIENT_SECRET="d-secret", OAUTH_SCOPE="d-scope"), environ={}
    )

    assert settings.oauth_clients["default"] == OAuthClientConfig("d-id", "d-secret", "d-scope")


def test_default_client_requires_both_id_and_secret(write_env: Callable[..., Path]) -> None:
    with pytest.raises(ConfigError, match="Both OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET"):
        load_settings(write_env(OAUTH_CLIENT_ID="only-id"), environ={})


def test_empty_environment_values_do_not_override(write_env: Callable[..., Path]) -> None:
    settings = load_settings(write_env(), environ={"API_BASE_URL": ""})

    assert settings.api_base_url == "https://api.example.test"


def test_environment_only_without_env_file() -> None:
    settings = load_settings(None, environ={key: value for key, value in BASE_ENV.items() if value})

    assert settings.env_name == "unit"
    assert settings.oauth_clients["client_a"].client_id == "id-a"


def test_environment_only_reports_missing_values() -> None:
    with pytest.raises(ConfigError, match="OAuth client"):
        load_settings(None, environ={})


@pytest.mark.parametrize(
    ("cli_value", "env_var_value", "default_exists", "expected_name"),
    [
        ("cli.env", "var.env", True, "cli.env"),
        (None, "var.env", True, "var.env"),
        (None, None, True, "default.env"),
        (None, None, False, None),
    ],
)
def test_env_file_precedence(
    tmp_path: Path, cli_value: str | None, env_var_value: str | None, default_exists: bool, expected_name: str | None
) -> None:
    default_path = tmp_path.joinpath("default.env")
    if default_exists:
        default_path.touch()

    resolved = resolve_env_file(cli_value, env_var_value, default_path)

    if expected_name is None:
        assert resolved is None
    else:
        assert resolved is not None
        assert resolved.name == expected_name
        assert resolved.is_absolute()


def test_resolve_oauth_client_by_name_is_case_insensitive(write_env: Callable[..., Path]) -> None:
    settings = load_settings(write_env(), environ={})

    assert settings.resolve_oauth_client(" Client_A ")[0] == "client_a"
    with pytest.raises(ConfigError):
        settings.resolve_oauth_client("unknown")


def test_parse_launch_args_handles_empty_value() -> None:
    assert parse_launch_args(None) == ()
    assert parse_launch_args("") == ()
