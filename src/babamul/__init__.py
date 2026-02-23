"""Babamul: A Python client for consuming ZTF/LSST alerts from Babamul Kafka
streams and interacting with the Babamul API.
"""

from . import api, jupyter, topics
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
from .models import (
    LsstAlert,
    LsstCandidate,
    ZtfAlert,
    ZtfCandidate,
    add_cross_matches,
)

__all__ = [
    "api",
    "topics",
    "jupyter",
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
    "add_cross_matches",
]

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"
