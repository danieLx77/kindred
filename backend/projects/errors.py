"""Application-facing provider failures, independent of HTTP responses."""

from enum import Enum


class ProviderFailure(Enum):
    INVALID_REQUEST = "invalid_request"
    AUTHENTICATION = "authentication"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    NETWORK = "network"
    INVALID_RESPONSE = "invalid_response"


class ProviderError(Exception):
    def __init__(self, reason: ProviderFailure) -> None:
        self.reason = reason
        super().__init__(f"Project provider failure: {reason.value}")
