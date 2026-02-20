"""Babamul: A Python client for consuming ZTF/LSST alerts from Babamul Kafka
streams and interacting with the Babamul API.
"""

from . import api, topics
from .api import (
    get_alerts,
    get_cutouts,
    get_object,
    get_profile,
    search_objects,
)
from .consumer import AlertConsumer
from .exceptions import (
    APIAuthenticationError,
    APIError,
    APINotFoundError,
    AuthenticationError,
    BabamulConnectionError,
    BabamulError,
    ConfigurationError,
    DeserializationError,
)
from .jupyter import scan_alerts
from .models import (
    LsstAlert,
    LsstCandidate,
    ZtfAlert,
    ZtfCandidate,
)

__all__ = [
    "api",
    "topics",
    "get_alerts",
    "get_cutouts",
    "get_object",
    "get_profile",
    "search_objects",
    "AlertConsumer",
    "APIAuthenticationError",
    "APIError",
    "APINotFoundError",
    "AuthenticationError",
    "BabamulConnectionError",
    "BabamulError",
    "ConfigurationError",
    "DeserializationError",
    "LsstAlert",
    "LsstCandidate",
    "ZtfAlert",
    "ZtfCandidate",
    "scan_alerts",
]

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"
