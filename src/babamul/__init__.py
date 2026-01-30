"""Babamul - Python client for consuming ZTF/LSST alerts from BABAMUL Kafka streams."""

from .api_client import (
    AlertCutouts,
    APIClient,
    KafkaCredential,
    ObjectSearchResult,
    UserProfile,
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
    "APIClient",
    # API Models
    "AlertCutouts",
    "ObjectSearchResult",
    "KafkaCredential",
    "UserProfile",
    # Alert Models
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
    "APIError",
    "APIAuthenticationError",
    "APINotFoundError",
    # Version
    "__version__",
]
