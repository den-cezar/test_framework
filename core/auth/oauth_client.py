"""
OAuth client credentials flow with shared token cache.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from core.auth.token_cache import SharedTokenCache, TokenRecord
from core.config.settings import FrameworkSettings
from core.logging.logger import Logger


class OAuthClient:
    """
    OAuth client for fetching access tokens.
    """

    def __init__(self, settings: FrameworkSettings, token_cache: SharedTokenCache) -> None:
        """
        Initialize the OAuth client.

        :param settings: Mandatory, Framework settings.
        :param token_cache: Mandatory, Shared token cache instance.
        """
        self.logger = Logger.get_logger("OAuth")
        self.logger.debug("Initializing OAuth client.")

        if not isinstance(settings, FrameworkSettings):
            raise ValueError("settings must be a FrameworkSettings instance.")
        if not isinstance(token_cache, SharedTokenCache):
            raise ValueError("token_cache must be a SharedTokenCache instance.")

        self.settings = settings
        self.token_cache = token_cache

    def get_access_token(self, scope_value: str | None = None, client_name: str | None = None) -> str:
        """
        Get a valid access token, refreshing when needed.

        :param scope_value: Optional, OAuth scope for the token.
        :param client_name: Optional, Override OAuth client name.
        :return: Access token string.
        """
        self.logger.debug("Fetching OAuth access token.")

        resolved_name, client_config = self.settings.resolve_oauth_client(client_name)
        resolved_scope = scope_value or client_config.scope

        cache_key = self._build_cache_key(resolved_name, client_config.client_id, resolved_scope)
        cached_token = self.token_cache.get_token(cache_key)
        if cached_token and not cached_token.is_expired():
            return cached_token.access_token

        token_record = self._request_token(client_config, resolved_scope)
        self.token_cache.set_token(cache_key, token_record)
        return token_record.access_token

    def _build_cache_key(self, client_name: str, client_id: str, scope_value: str | None) -> str:
        """
        Build a token cache key.

        :param client_name: Mandatory, OAuth client name.
        :param client_id: Mandatory, OAuth client id.
        :param scope_value: Optional, OAuth scope for the token.
        :return: Cache key string.
        """
        self.logger.debug("Building OAuth cache key.")

        scope_part = scope_value or "default"
        return f"{self.settings.env_name}:{client_name}:{client_id}:{scope_part}"

    def _request_token(self, client_config: Any, scope_value: str | None) -> TokenRecord:
        """
        Request a new token from the OAuth server.

        :param client_config: Mandatory, OAuth client configuration.
        :param scope_value: Optional, OAuth scope for the token.
        :return: TokenRecord instance.
        """
        self.logger.debug("Requesting new OAuth token.")

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_config.client_id,
            "client_secret": client_config.client_secret,
        }
        if scope_value:
            payload["scope"] = scope_value

        response = httpx.post(self.settings.oauth_token_url, data=payload, timeout=30)
        if response.status_code >= 400:
            raise RuntimeError(f"Token request failed: {response.status_code} {response.text}")

        token_json: dict[str, Any] = response.json()
        access_token = str(token_json.get("access_token", ""))
        expires_in = int(token_json.get("expires_in", 0))
        if not access_token or expires_in <= 0:
            raise RuntimeError("Invalid token response from OAuth server.")

        expires_at = time.time() + expires_in
        return TokenRecord(access_token=access_token, expires_at=expires_at)
