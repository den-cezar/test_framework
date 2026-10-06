"""
Domain service for API operations.
"""

from __future__ import annotations

from adapters.http_client import HttpClient
from domain.api.models import IDENTITY_CLAIMS, IdentityClaim, ServiceStatus


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

    def get_identity_claim_list(self, client_name: str | None = None) -> list[IdentityClaim]:
        """
        Call the protected identity endpoint and validate the response against the claims contract.

        :param client_name: Optional, OAuth client to authenticate as.
        :return: Validated claims, in response order.
        """
        response = self.http_client.request("GET", self.IDENTITY_PATH, client_name=client_name)
        response.raise_for_status()
        return IDENTITY_CLAIMS.validate_json(response.content)

    def get_identity_claims(self, client_name: str | None = None) -> dict[str, str]:
        """
        Call the protected identity endpoint and return the token claims it echoes back.

        :param client_name: Optional, OAuth client to authenticate as.
        :return: Mapping of claim type to value.
        """
        return {claim.type: claim.value for claim in self.get_identity_claim_list(client_name)}

    def identity_status_with_authorization(self, authorization: str | None) -> int:
        """
        Call the protected identity endpoint with a raw Authorization header (or none), for negative tests.

        :param authorization: Optional, Authorization header value; None sends no header.
        :return: HTTP status code.
        """
        headers = {"Authorization": authorization} if authorization is not None else None
        return self.http_client.request_public("GET", self.IDENTITY_PATH, headers=headers).status_code

    def get_service_status(self, url_value: str) -> ServiceStatus:
        """
        Fetch and validate a Statuspage.io status document.

        :param url_value: Mandatory, Absolute URL of `/api/v2/status.json`.
        :return: Validated service status.
        """
        response = self.http_client.request_public("GET", url_value)
        response.raise_for_status()
        return ServiceStatus.model_validate_json(response.content)

    def public_health_check(self, url_value: str) -> int:
        """
        Execute a public health check endpoint.

        :param url_value: Mandatory, Absolute URL.
        :return: HTTP status code.
        """
        return self.http_client.request_public("GET", url_value).status_code
