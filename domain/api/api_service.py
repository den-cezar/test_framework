"""
Domain service for API operations.
"""

from __future__ import annotations

from adapters.http_client import HttpClient


class ApiService:
    """
    Domain API service: business-level operations on top of the HTTP adapter.
    """

    IDENTITY_PATH = "/api/test"

    def __init__(self, http_client: HttpClient) -> None:
        """
        Initialize the API service.

        :param http_client: Mandatory, HTTP client adapter.
        """
        self.http_client = http_client

    def get_identity_claims(self, client_name: str | None = None) -> dict[str, str]:
        """
        Call the protected identity endpoint and return the token claims it echoes back.

        :param client_name: Optional, OAuth client to authenticate as.
        :return: Mapping of claim type to value.
        """
        response = self.http_client.request("GET", self.IDENTITY_PATH, client_name=client_name)
        response.raise_for_status()
        return {str(claim["type"]): str(claim["value"]) for claim in response.json()}

    def public_health_check(self, url_value: str) -> int:
        """
        Execute a public health check endpoint.

        :param url_value: Mandatory, Absolute URL.
        :return: HTTP status code.
        """
        return self.http_client.request_public("GET", url_value).status_code
