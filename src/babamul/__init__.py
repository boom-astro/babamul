"""Babamul: A Python client for consuming ZTF/LSST alerts from Babamul Kafka
streams and interacting with the Babamul API.
"""

from . import api, topics
from .consumer import AlertConsumer
from .exceptions import (
    AuthenticationError,
    BabamulConnectionError,
    BabamulError,
    ConfigurationError,
    DeserializationError,
)
from .models import (
    LsstAlert,
    LsstCandidate,
    LsstPhotometry,
    ZtfAlert,
    ZtfCandidate,
    ZtfPhotometry,
)

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = [
    # Modules
    "api",
    "topics",
    # Main classes
    "AlertConsumer",
    # Models
    "ZtfAlert",
    "ZtfPhotometry",
    "ZtfCandidate",
    "LsstCandidate",
    "LsstPhotometry",
    "LsstAlert",
    # Exceptions
    "BabamulError",
    "AuthenticationError",
    "BabamulConnectionError",
    "DeserializationError",
    "ConfigurationError",
    # Version
    "__version__",
]
