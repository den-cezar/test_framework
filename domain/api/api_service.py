"""
Domain service for API operations.
"""

from __future__ import annotations

from adapters.http_client import HttpClient
from core.logging.logger import Logger


class ApiService:
    """
    Domain API service wrapper.
    """

    def __init__(self, http_client: HttpClient) -> None:
        """
        Initialize the API service.

        :param http_client: Mandatory, HTTP client adapter.
        """
        logger = Logger.get_logger("ApiService")
        logger.debug("Initializing ApiService.")

        if not isinstance(http_client, HttpClient):
            raise ValueError("http_client must be an HttpClient instance.")
        self.http_client = http_client

    def health_check(self) -> int:
        """
        Execute a health check endpoint.

        :return: HTTP status code.
        """
        logger = Logger.get_logger("ApiService")
        logger.debug("Running API health check.")

        response = self.http_client.request("GET", "/health")
        return response.status_code

    def public_health_check(self, url_value: str) -> int:
        """
        Execute a public health check endpoint.

        :param url_value: Mandatory, Absolute URL.
        :return: HTTP status code.
        """
        logger = Logger.get_logger("ApiService")
        logger.debug("Running public API health check.")

        response = self.http_client.request_public("GET", url_value)
        return response.status_code
