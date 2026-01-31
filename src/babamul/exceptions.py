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


class APIError(BabamulError):
    """Raised when an API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""

    pass


class APINotFoundError(APIError):
    """Raised when a requested resource is not found."""

    pass
