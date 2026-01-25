"""Custom exceptions for boom-alerts."""


class BoomError(Exception):
    """Base exception for all boom-alerts errors."""

    pass


class AuthenticationError(BoomError):
    """Raised when authentication to Kafka fails."""

    pass


class ConnectionError(BoomError):
    """Raised when connection to Kafka server fails."""

    pass


class DeserializationError(BoomError):
    """Raised when Avro deserialization fails."""

    pass


class ConfigurationError(BoomError):
    """Raised when configuration is invalid."""

    pass
