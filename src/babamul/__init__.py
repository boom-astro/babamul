"""Babamul: A Python client for consuming ZTF/LSST alerts from Babamul Kafka
streams and interacting with the Babamul API.
"""

from . import api, topics
from .api import (
    create_kafka_credential,
    delete_kafka_credential,
    get_alerts,
    get_cutouts,
    get_object,
    get_profile,
    list_kafka_credentials,
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
    # API functions
    "get_alerts",
    "get_cutouts",
    "get_object",
    "get_profile",
    "search_objects",
    "create_kafka_credential",
    "list_kafka_credentials",
    "delete_kafka_credential",
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
    "APIError",
    "APIAuthenticationError",
    "APINotFoundError",
    # Version
    "__version__",
]
