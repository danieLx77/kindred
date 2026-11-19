"""GlobalGiving adapters for the Kindred project provider contract."""

from .detail import GlobalGivingProjectProvider
from .discovery import GlobalGivingDiscoveryAdapter

__all__ = ["GlobalGivingDiscoveryAdapter", "GlobalGivingProjectProvider"]
