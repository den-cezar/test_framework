"""
API contracts. Responses are parsed into these models, so every API test also validates the contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, TypeAdapter


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class IdentityClaim(_Contract):
    """One claim echoed by the identity provider's protected endpoint."""

    type: str
    value: str


IDENTITY_CLAIMS = TypeAdapter(list[IdentityClaim])
REQUIRED_IDENTITY_CLAIMS = frozenset({"iss", "aud", "exp", "iat", "nbf", "scope", "client_id"})


class StatusPage(_Contract):
    """Statuspage.io page metadata."""

    id: str
    name: str
    url: str
    time_zone: str
    updated_at: datetime


class StatusIndicator(_Contract):
    """Overall service status."""

    indicator: Literal["none", "minor", "major", "critical", "maintenance"]
    description: str


class ServiceStatus(_Contract):
    """Statuspage.io `/api/v2/status.json` response."""

    page: StatusPage
    status: StatusIndicator


class Fruit(_Contract):
    """Item of the Playwright api-mocking demo `/api/v1/fruits` response."""

    name: str
    id: int


FRUITS = TypeAdapter(list[Fruit])
