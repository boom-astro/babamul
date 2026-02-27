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


def __getattr__(name: str):
    """Lazy import for optional submodules.

    Submodules listed here are only imported when explicitly accessed,
    rather than at package load time.
    """
    if name == "jupyter":
        from . import jupyter

        return jupyter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"
