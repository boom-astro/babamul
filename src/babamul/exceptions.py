"""Custom exceptions for Babamul alerts."""


class BabamulError(Exception):
    """Base exception for all Babamul alerts errors."""

    pass


class AuthenticationError(BabamulError):
    """Raised when authentication to Kafka fails."""

    pass


class BabamulConnectionError(BabamulError):
    """Raised when connection to Kafka server fails."""

    pass


class DeserializationError(BabamulError):
    """Raised when Avro deserialization fails."""

    pass


class ConfigurationError(BabamulError):
    """Raised when configuration is invalid."""

    pass
