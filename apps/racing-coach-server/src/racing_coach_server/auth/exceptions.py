"""Authentication-specific exceptions."""

from racing_coach_server.exceptions import RacingCoachException


class AuthException(RacingCoachException):
    """Base exception for authentication errors."""


class UserAlreadyExistsError(AuthException):
    """Raised when attempting to register with an existing email."""


class InvalidCredentialsError(AuthException):
    """Raised when login credentials are invalid."""


class SessionNotFoundError(AuthException):
    """Raised when a session or token is not found."""


class AuthenticationRequiredError(AuthException):
    """Raised when authentication is required but not provided."""


class DeviceAuthorizationPendingError(AuthException):
    """Raised when device authorization is still pending."""


class DeviceAuthorizationDeniedError(AuthException):
    """Raised when device authorization was denied."""


class DeviceAuthorizationExpiredError(AuthException):
    """Raised when device authorization has expired."""
