"""
HTTP client adapter for API tests.
"""

from __future__ import annotations

from typing import Any

import httpx

from core.auth.oauth_client import OAuthClient
from core.config.settings import FrameworkSettings
from core.logging.logger import Logger

logger = Logger.get_logger("HttpClient")
MAX_LOGGED_BODY_CHARS = 1000


def _log_request(request: httpx.Request) -> None:
    """Log the outgoing request line. Headers are not logged because they carry the bearer token."""
    logger.info("--> %s %s", request.method, request.url)


def _log_response(response: httpx.Response) -> None:
    """Log the response status and a truncated body."""
    response.read()
    logger.info("<-- %s %s %s", response.status_code, response.request.method, response.request.url)
    logger.debug("Response body: %s", response.text[:MAX_LOGGED_BODY_CHARS])


class HttpClient:
    """
    HTTP client with a pooled connection, OAuth bearer auth and request/response logging.
    """

    def __init__(
        self, settings: FrameworkSettings, oauth_client: OAuthClient, transport: httpx.BaseTransport | None = None
    ) -> None:
        """
        Initialize the HTTP client.

        :param settings: Mandatory, Framework settings.
        :param oauth_client: Mandatory, OAuth client.
        :param transport: Optional, Custom transport (e.g. httpx.MockTransport in unit tests).
        """
        self.oauth_client = oauth_client
        self._client = httpx.Client(
            base_url=settings.api_base_url,
            timeout=settings.http_timeout_seconds,
            transport=transport,
            event_hooks={"request": [_log_request], "response": [_log_response]},
        )

    def request(
        self, method_name: str, path_value: str, json_body: dict[str, Any] | None = None, client_name: str | None = None
    ) -> httpx.Response:
        """
        Execute a request against API_BASE_URL with an OAuth bearer token.

        :param method_name: Mandatory, HTTP method name.
        :param path_value: Mandatory, Path relative to API_BASE_URL.
        :param json_body: Optional, JSON body payload.
        :param client_name: Optional, OAuth client to authenticate as.
        :return: httpx.Response instance.
        """
        access_token = self.oauth_client.get_access_token(client_name=client_name)
        return self._client.request(
            method_name.upper(), path_value, json=json_body, headers={"Authorization": f"Bearer {access_token}"}
        )

    def request_public(
        self,
        method_name: str,
        url_value: str,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Execute a request without OAuth.

        :param method_name: Mandatory, HTTP method name.
        :param url_value: Mandatory, Absolute URL or path relative to API_BASE_URL.
        :param json_body: Optional, JSON body payload.
        :param headers: Optional, Extra headers.
        :return: httpx.Response instance.
        """
        return self._client.request(method_name.upper(), url_value, json=json_body, headers=headers)

    def close(self) -> None:
        """
        Close the underlying connection pool.
        """
        self._client.close()
