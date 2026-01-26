"""Babamul - Python client for consuming ZTF/LSST alerts from BABAMUL Kafka streams."""

from .consumer import AlertConsumer
from .exceptions import (
    AuthenticationError,
    BabamulError,
    ConfigurationError,
    ConnectionError,
    DeserializationError,
)
from .models import (
    BabamulLsstAlert,
    LsstCandidate,
    LsstPhotometry,
    BabamulZtfAlert,
    ZtfCandidate,
    ZtfPhotometry,
)

__version__ = "0.1.0"

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
    "ConnectionError",
    "DeserializationError",
    "ConfigurationError",
    # Version
    "__version__",
]
