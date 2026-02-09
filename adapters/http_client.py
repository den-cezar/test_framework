"""
HTTP client adapter for API tests.
"""

from __future__ import annotations

from typing import Any

import httpx

from core.auth.oauth_client import OAuthClient
from core.config.settings import FrameworkSettings
from core.logging.logger import Logger


class HttpClient:
    """
    Simple HTTP client with OAuth authentication.
    """

    def __init__(self, settings: FrameworkSettings, oauth_client: OAuthClient) -> None:
        """
        Initialize the HTTP client.

        :param settings: Mandatory, Framework settings.
        :param oauth_client: Mandatory, OAuth client.
        """
        logger = Logger.get_logger("HttpClient")
        logger.debug("Initializing HTTP client.")

        if not isinstance(settings, FrameworkSettings):
            raise ValueError("settings must be a FrameworkSettings instance.")
        if not isinstance(oauth_client, OAuthClient):
            raise ValueError("oauth_client must be an OAuthClient instance.")

        self.settings = settings
        self.oauth_client = oauth_client

    def request(self, method_name: str, path_value: str, json_body: dict[str, Any] | None = None) -> httpx.Response:
        """
        Execute an HTTP request with OAuth token.

        :param method_name: Mandatory, HTTP method name.
        :param path_value: Mandatory, API path.
        :param json_body: Optional, JSON body payload.
        :return: httpx.Response instance.
        """
        logger = Logger.get_logger("HttpClient")
        logger.debug("Executing HTTP request.")

        if not isinstance(method_name, str) or not method_name:
            raise ValueError("method_name must be a non-empty string.")
        if not isinstance(path_value, str) or not path_value:
            raise ValueError("path_value must be a non-empty string.")

        access_token = self.oauth_client.get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        url_value = f"{self.settings.api_base_url.rstrip('/')}/{path_value.lstrip('/')}"

        response = httpx.request(method_name.upper(), url_value, json=json_body, headers=headers, timeout=30)
        return response

    def request_public(
        self,
        method_name: str,
        url_value: str,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Execute an HTTP request without OAuth.

        :param method_name: Mandatory, HTTP method name.
        :param url_value: Mandatory, Absolute URL.
        :param json_body: Optional, JSON body payload.
        :param headers: Optional, Extra headers.
        :return: httpx.Response instance.
        """
        logger = Logger.get_logger("HttpClient")
        logger.debug("Executing public HTTP request.")

        if not isinstance(method_name, str) or not method_name:
            raise ValueError("method_name must be a non-empty string.")
        if not isinstance(url_value, str) or not url_value:
            raise ValueError("url_value must be a non-empty string.")

        response = httpx.request(method_name.upper(), url_value, json=json_body, headers=headers, timeout=30)
        return response
