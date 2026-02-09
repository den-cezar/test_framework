"""
Configuration loading for the new test framework.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from core.logging.logger import Logger


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
    oauth_token_url: str
    oauth_client_name: str | None
    oauth_clients: Mapping[str, OAuthClientConfig]
    token_cache_path: Path
    log_console_level: str
    log_file_level: str
    timezone: str

    def validate(self) -> None:
        """
        Validate configuration values.
        """
        logger = Logger.get_logger("Config")
        logger.debug("Validating framework settings.")

        if not self.env_name:
            raise ValueError("env_name must be provided.")
        if not self.api_base_url:
            raise ValueError("api_base_url must be provided.")
        if not self.oauth_token_url:
            raise ValueError("oauth_token_url must be provided.")
        if not isinstance(self.oauth_clients, Mapping) or not self.oauth_clients:
            raise ValueError("oauth_clients must be a non-empty mapping.")
        if not isinstance(self.token_cache_path, Path):
            raise ValueError("token_cache_path must be a Path.")
        if self.timezone not in {"UTC", "LOCAL"}:
            raise ValueError("timezone must be UTC or LOCAL.")

    def resolve_oauth_client(self, client_name: str | None = None) -> tuple[str, OAuthClientConfig]:
        """
        Resolve the OAuth client configuration by name.

        :param client_name: Optional, Override client name.
        :return: Tuple of normalized client name and configuration.
        """
        if client_name:
            name = _normalize_client_name(client_name)
            if name not in self.oauth_clients:
                raise ValueError(f"OAuth client name not found: {name}")
            return name, self.oauth_clients[name]

        if self.oauth_client_name:
            name = _normalize_client_name(self.oauth_client_name)
            if name not in self.oauth_clients:
                raise ValueError(f"OAuth client name not found: {name}")
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
    logger = Logger.get_logger("Config")
    logger.debug("Resolving required config value.")

    if not isinstance(key_name, str) or not key_name:
        raise ValueError("key_name must be a non-empty string.")
    if key_name not in raw_values or not raw_values.get(key_name):
        raise ValueError(f"Missing required config value: {key_name}")
    return str(raw_values[key_name])


def _normalize_client_name(name: str) -> str:
    """
    Normalize and validate an OAuth client name.

    :param name: Mandatory, The client name value.
    :return: Normalized client name.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("OAuth client name must be a non-empty string.")
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
            raise ValueError("Both OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET must be set for default client.")
        clients["default"] = OAuthClientConfig(
            client_id=str(default_id),
            client_secret=str(default_secret),
            scope=str(default_scope) if default_scope else None,
        )

    # Name-based client definitions: OAUTH_CLIENT_NAME_<SUFFIX>=client_a
    # with OAUTH_CLIENT_ID_<SUFFIX>, OAUTH_CLIENT_SECRET_<SUFFIX>, OAUTH_SCOPE_<SUFFIX>
    for key, value in raw_values.items():
        if not key.startswith("OAUTH_CLIENT_NAME_"):
            continue
        suffix = key[len("OAUTH_CLIENT_NAME_") :]
        name = _normalize_client_name(str(value))
        if name in clients:
            raise ValueError(f"Duplicate OAuth client name: {name}")

        client_id_key = f"OAUTH_CLIENT_ID_{suffix}"
        client_secret_key = f"OAUTH_CLIENT_SECRET_{suffix}"
        client_id_value = raw_values.get(client_id_key)
        client_secret_value = raw_values.get(client_secret_key)
        if not client_id_value or not client_secret_value:
            raise ValueError(f"Missing required config value: {client_id_key} or {client_secret_key}")

        scope_key = f"OAUTH_SCOPE_{suffix}"
        scope_value = raw_values.get(scope_key)

        clients[name] = OAuthClientConfig(
            client_id=str(client_id_value),
            client_secret=str(client_secret_value),
            scope=str(scope_value) if scope_value else None,
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
            raise ValueError(f"Duplicate OAuth client name: {name}")

        secret_key = f"OAUTH_CLIENT_SECRET_{suffix}"
        secret_value = raw_values.get(secret_key)
        if not secret_value:
            raise ValueError(f"Missing required config value: {secret_key}")

        scope_key = f"OAUTH_SCOPE_{suffix}"
        scope_value = raw_values.get(scope_key)

        clients[name] = OAuthClientConfig(
            client_id=str(value),
            client_secret=str(secret_value),
            scope=str(scope_value) if scope_value else None,
        )

    if not clients:
        raise ValueError("At least one OAuth client configuration must be provided.")

    raw_default_name = raw_values.get("OAUTH_CLIENT_NAME")
    if raw_default_name:
        default_name = _normalize_client_name(raw_default_name)
        if default_name not in clients:
            raise ValueError(f"OAuth client name not found: {default_name}")
        return default_name, clients

    return None, clients


def load_settings(env_file_path: Path) -> FrameworkSettings:
    """
    Load framework settings from an env file.

    :param env_file_path: Mandatory, Path to the env file.
    :return: FrameworkSettings instance.
    """
    logger = Logger.get_logger("Config")
    logger.debug("Loading framework settings.")

    if not isinstance(env_file_path, Path):
        raise ValueError("env_file_path must be a Path.")
    if not env_file_path.exists():
        raise FileNotFoundError(f"Env file not found: {env_file_path}")

    raw_values = {key: value for key, value in dotenv_values(env_file_path).items() if value is not None}

    oauth_client_name, oauth_clients = _load_oauth_clients(raw_values)

    settings = FrameworkSettings(
        env_name=_get_required(raw_values, "ENV_NAME"),
        api_base_url=_get_required(raw_values, "API_BASE_URL"),
        oauth_token_url=_get_required(raw_values, "OAUTH_TOKEN_URL"),
        oauth_client_name=oauth_client_name,
        oauth_clients=oauth_clients,
        token_cache_path=Path(_get_required(raw_values, "TOKEN_CACHE_PATH")),
        log_console_level=_get_required(raw_values, "LOG_CONSOLE_LEVEL"),
        log_file_level=_get_required(raw_values, "LOG_FILE_LEVEL"),
        timezone=_get_required(raw_values, "TIMEZONE"),
    )

    settings.validate()
    return settings
