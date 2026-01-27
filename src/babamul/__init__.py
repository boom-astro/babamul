"""Babamul - Python client for consuming ZTF/LSST alerts from BABAMUL Kafka streams."""

from .consumer import AlertConsumer
from .exceptions import (
    AuthenticationError,
    BabamulConnectionError,
    BabamulError,
    ConfigurationError,
    DeserializationError,
)
from .models import (
    BabamulLsstAlert,
    BabamulZtfAlert,
    LsstCandidate,
    LsstPhotometry,
    ZtfCandidate,
    ZtfPhotometry,
)

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = [
    # Main classes
    "AlertConsumer",
    # Models
    "BabamulZtfAlert",
    "ZtfPhotometry",
    "ZtfCandidate",
    "LsstCandidate",
    "LsstPhotometry",
    "BabamulLsstAlert",
    # Exceptions
    "BabamulError",
    "AuthenticationError",
    "BabamulConnectionError",
    "DeserializationError",
    "ConfigurationError",
    # Version
    "__version__",
]
