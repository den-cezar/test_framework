"""
Configuration loading for the new test framework.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from core.errors import ConfigError

LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
DEFAULT_HTTP_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class OAuthClientConfig:
    """
    OAuth client configuration.
    """

    client_id: str
    client_secret: str
    scope: str | None = None


@dataclass(frozen=True)
class FrameworkSettings:
    """
    Immutable framework configuration settings.
    """

    env_name: str
    api_base_url: str
    ui_base_url: str
    oauth_token_url: str
    oauth_client_name: str | None
    oauth_clients: Mapping[str, OAuthClientConfig]
    token_cache_path: Path
    log_console_level: str
    log_file_level: str
    timezone: str
    http_timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS
    playwright_headless: bool = True
    playwright_launch_args: tuple[str, ...] = ()

    def validate(self) -> None:
        """
        Validate configuration values.
        """
        if not self.oauth_clients:
            raise ConfigError("At least one OAuth client configuration must be provided.")
        if self.timezone not in {"UTC", "LOCAL"}:
            raise ConfigError("TIMEZONE must be UTC or LOCAL.")
        for key_name, level in (("LOG_CONSOLE_LEVEL", self.log_console_level), ("LOG_FILE_LEVEL", self.log_file_level)):
            if level not in LOG_LEVELS:
                raise ConfigError(f"{key_name} must be one of {sorted(LOG_LEVELS)}, got: {level}")
        if self.http_timeout_seconds <= 0:
            raise ConfigError("HTTP_TIMEOUT_SECONDS must be positive.")

    def resolve_oauth_client(self, client_name: str | None = None) -> tuple[str, OAuthClientConfig]:
        """
        Resolve the OAuth client configuration by name.

        :param client_name: Optional, Override client name.
        :return: Tuple of normalized client name and configuration.
        """
        if client_name:
            name = _normalize_client_name(client_name)
            if name not in self.oauth_clients:
                raise ConfigError(f"OAuth client name not found: {name}")
            return name, self.oauth_clients[name]

        if self.oauth_client_name:
            name = _normalize_client_name(self.oauth_client_name)
            if name not in self.oauth_clients:
                raise ConfigError(f"OAuth client name not found: {name}")
            return name, self.oauth_clients[name]

        if len(self.oauth_clients) == 1:
            name, config = next(iter(self.oauth_clients.items()))
            return name, config

        name = sorted(self.oauth_clients.keys())[0]
        return name, self.oauth_clients[name]


def _get_required(raw_values: Mapping[str, str], key_name: str) -> str:
    """
    Get a required value from config mapping.

    :param raw_values: Mandatory, The key/value mapping.
    :param key_name: Mandatory, The key to retrieve.
    :return: The value for the specified key.
    """
    value = raw_values.get(key_name)
    if not value:
        raise ConfigError(f"Missing required config value: {key_name}")
    return value


def _parse_bool(raw_values: Mapping[str, str], key_name: str, default: bool) -> bool:
    """
    Parse an optional boolean config value.

    :param raw_values: Mandatory, The key/value mapping.
    :param key_name: Mandatory, The key to retrieve.
    :param default: Mandatory, Value used when the key is absent.
    :return: Parsed boolean.
    """
    value = raw_values.get(key_name)
    if not value:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise ConfigError(f"{key_name} must be a boolean, got: {value}")


def _parse_float(raw_values: Mapping[str, str], key_name: str, default: float) -> float:
    """
    Parse an optional float config value.

    :param raw_values: Mandatory, The key/value mapping.
    :param key_name: Mandatory, The key to retrieve.
    :param default: Mandatory, Value used when the key is absent.
    :return: Parsed float.
    """
    value = raw_values.get(key_name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ConfigError(f"{key_name} must be a number, got: {value}") from exc


def parse_launch_args(raw_value: str | None) -> tuple[str, ...]:
    """
    Parse comma-separated browser launch args.

    :param raw_value: Optional, Raw config value.
    :return: Tuple of args.
    """
    if not raw_value:
        return ()
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def _normalize_client_name(name: str) -> str:
    """
    Normalize and validate an OAuth client name.

    :param name: Mandatory, The client name value.
    :return: Normalized client name.
    """
    if not name.strip():
        raise ConfigError("OAuth client name must be a non-empty string.")
    return name.strip().lower()


def _load_oauth_clients(raw_values: Mapping[str, str]) -> tuple[str | None, dict[str, OAuthClientConfig]]:
    """
    Load OAuth client configurations from raw values.

    :param raw_values: Mandatory, The key/value mapping.
    :return: Tuple of default client name and client config mapping.
    """
    clients: dict[str, OAuthClientConfig] = {}

    default_id = raw_values.get("OAUTH_CLIENT_ID")
    default_secret = raw_values.get("OAUTH_CLIENT_SECRET")
    default_scope = raw_values.get("OAUTH_SCOPE")
    if default_id or default_secret:
        if not default_id or not default_secret:
            raise ConfigError("Both OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET must be set for default client.")
        clients["default"] = OAuthClientConfig(
            client_id=default_id,
            client_secret=default_secret,
            scope=default_scope or None,
        )

    # Name-based client definitions: OAUTH_CLIENT_NAME_<SUFFIX>=client_a
    # with OAUTH_CLIENT_ID_<SUFFIX>, OAUTH_CLIENT_SECRET_<SUFFIX>, OAUTH_SCOPE_<SUFFIX>
    for key, value in raw_values.items():
        if not key.startswith("OAUTH_CLIENT_NAME_"):
            continue
        suffix = key[len("OAUTH_CLIENT_NAME_") :]
        name = _normalize_client_name(value)
        if name in clients:
            raise ConfigError(f"Duplicate OAuth client name: {name}")

        client_id_key = f"OAUTH_CLIENT_ID_{suffix}"
        client_secret_key = f"OAUTH_CLIENT_SECRET_{suffix}"
        client_id_value = raw_values.get(client_id_key)
        client_secret_value = raw_values.get(client_secret_key)
        if not client_id_value or not client_secret_value:
            raise ConfigError(f"Missing required config value: {client_id_key} or {client_secret_key}")

        clients[name] = OAuthClientConfig(
            client_id=client_id_value,
            client_secret=client_secret_value,
            scope=raw_values.get(f"OAUTH_SCOPE_{suffix}") or None,
        )

    # Legacy client definitions: OAUTH_CLIENT_ID_<SUFFIX> with optional OAUTH_SCOPE_<SUFFIX>
    for key, value in raw_values.items():
        if not key.startswith("OAUTH_CLIENT_ID_"):
            continue
        suffix = key[len("OAUTH_CLIENT_ID_") :]
        if f"OAUTH_CLIENT_NAME_{suffix}" in raw_values:
            continue
        name = _normalize_client_name(suffix)
        if name in clients:
            raise ConfigError(f"Duplicate OAuth client name: {name}")

        secret_key = f"OAUTH_CLIENT_SECRET_{suffix}"
        secret_value = raw_values.get(secret_key)
        if not secret_value:
            raise ConfigError(f"Missing required config value: {secret_key}")

        clients[name] = OAuthClientConfig(
            client_id=value,
            client_secret=secret_value,
            scope=raw_values.get(f"OAUTH_SCOPE_{suffix}") or None,
        )

    if not clients:
        raise ConfigError("At least one OAuth client configuration must be provided.")

    raw_default_name = raw_values.get("OAUTH_CLIENT_NAME")
    if raw_default_name:
        default_name = _normalize_client_name(raw_default_name)
        if default_name not in clients:
            raise ConfigError(f"OAuth client name not found: {default_name}")
        return default_name, clients

    return None, clients


def resolve_env_file(cli_value: str | None, env_var_value: str | None, default_path: Path) -> Path | None:
    """
    Resolve the env file path. Precedence: --env-file option, then ENV_FILE variable, then the default if it exists.

    :param cli_value: Optional, Value of the --env-file option.
    :param env_var_value: Optional, Value of the ENV_FILE environment variable.
    :param default_path: Mandatory, Fallback path; skipped when absent (e.g. in CI).
    :return: Absolute path to the env file, or None to rely on environment variables only.
    """
    chosen = cli_value or env_var_value
    if chosen:
        return Path(chosen).expanduser().resolve()
    return default_path if default_path.is_file() else None


def load_settings(env_file_path: Path | None, environ: Mapping[str, str] | None = None) -> FrameworkSettings:
    """
    Load framework settings. Non-empty process environment variables override values from the env file.

    :param env_file_path: Optional, Path to the env file; None to use environment variables only.
    :param environ: Optional, Environment to overlay; defaults to os.environ.
    :return: FrameworkSettings instance.
    """
    file_values: dict[str, str] = {}
    if env_file_path is not None:
        if not env_file_path.is_file():
            raise ConfigError(f"Env file not found: {env_file_path}")
        file_values = {key: value for key, value in dotenv_values(env_file_path).items() if value is not None}

    env_values = {key: value for key, value in (os.environ if environ is None else environ).items() if value}
    raw_values = {**file_values, **env_values}

    oauth_client_name, oauth_clients = _load_oauth_clients(raw_values)

    settings = FrameworkSettings(
        env_name=_get_required(raw_values, "ENV_NAME"),
        api_base_url=_get_required(raw_values, "API_BASE_URL"),
        ui_base_url=_get_required(raw_values, "UI_BASE_URL"),
        oauth_token_url=_get_required(raw_values, "OAUTH_TOKEN_URL"),
        oauth_client_name=oauth_client_name,
        oauth_clients=oauth_clients,
        token_cache_path=Path(_get_required(raw_values, "TOKEN_CACHE_PATH")),
        log_console_level=_get_required(raw_values, "LOG_CONSOLE_LEVEL").upper(),
        log_file_level=_get_required(raw_values, "LOG_FILE_LEVEL").upper(),
        timezone=_get_required(raw_values, "TIMEZONE"),
        http_timeout_seconds=_parse_float(raw_values, "HTTP_TIMEOUT_SECONDS", DEFAULT_HTTP_TIMEOUT_SECONDS),
        playwright_headless=_parse_bool(raw_values, "PLAYWRIGHT_HEADLESS", True),
        playwright_launch_args=parse_launch_args(raw_values.get("PLAYWRIGHT_LAUNCH_ARGS")),
    )

    settings.validate()
    return settings
