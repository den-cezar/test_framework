"""
OAuth client credentials flow with shared token cache.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from core.auth.token_cache import SharedTokenCache, TokenRecord
from core.config.settings import FrameworkSettings, OAuthClientConfig
from core.errors import AuthError
from core.logging.logger import Logger

logger = Logger.get_logger("OAuth")


class OAuthClient:
    """
    OAuth client-credentials flow backed by the shared token cache.
    """

    def __init__(
        self, settings: FrameworkSettings, token_cache: SharedTokenCache, http: httpx.Client | None = None
    ) -> None:
        """
        Initialize the OAuth client.

        :param settings: Mandatory, Framework settings.
        :param token_cache: Mandatory, Shared token cache instance.
        :param http: Optional, HTTP client for the token endpoint (injected in unit tests).
        """
        self.settings = settings
        self.token_cache = token_cache
        self.http = http or httpx.Client(timeout=settings.http_timeout_seconds)

    def get_access_token(self, scope_value: str | None = None, client_name: str | None = None) -> str:
        """
        Get a valid access token, refreshing when needed.

        :param scope_value: Optional, OAuth scope for the token.
        :param client_name: Optional, Override OAuth client name.
        :return: Access token string.
        """
        resolved_name, client_config = self.settings.resolve_oauth_client(client_name)
        resolved_scope = scope_value or client_config.scope
        cache_key = self._build_cache_key(resolved_name, client_config.client_id, resolved_scope)
        record = self.token_cache.get_or_create(cache_key, lambda: self._request_token(client_config, resolved_scope))
        return record.access_token

    def close(self) -> None:
        """
        Close the underlying HTTP client.
        """
        self.http.close()

    def _build_cache_key(self, client_name: str, client_id: str, scope_value: str | None) -> str:
        """
        Build a token cache key.

        :param client_name: Mandatory, OAuth client name.
        :param client_id: Mandatory, OAuth client id.
        :param scope_value: Optional, OAuth scope for the token.
        :return: Cache key string.
        """
        return f"{self.settings.env_name}:{client_name}:{client_id}:{scope_value or 'default'}"

    def _request_token(self, client_config: OAuthClientConfig, scope_value: str | None) -> TokenRecord:
        """
        Request a new token from the OAuth server.

        :param client_config: Mandatory, OAuth client configuration.
        :param scope_value: Optional, OAuth scope for the token.
        :return: TokenRecord instance.
        """
        logger.info("Requesting OAuth token for client_id=%s scope=%s.", client_config.client_id, scope_value)

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_config.client_id,
            "client_secret": client_config.client_secret,
        }
        if scope_value:
            payload["scope"] = scope_value

        response = self.http.post(self.settings.oauth_token_url, data=payload)
        if response.is_error:
            raise AuthError(f"Token request failed: {response.status_code} {response.text}")

        token_json: dict[str, Any] = response.json()
        access_token = str(token_json.get("access_token", ""))
        expires_in = int(token_json.get("expires_in", 0))
        if not access_token or expires_in <= 0:
            raise AuthError("Invalid token response from OAuth server.")

        return TokenRecord(access_token=access_token, expires_at=time.time() + expires_in)
