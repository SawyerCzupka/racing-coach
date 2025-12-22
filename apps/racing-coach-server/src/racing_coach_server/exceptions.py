"""Base application exceptions for Racing Coach Server."""


class RacingCoachException(Exception):
    """Base exception for all Racing Coach application errors."""

    def __init__(self, message: str = "An error occurred", status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(RacingCoachException):
    """Base exception for resource not found errors."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ValidationError(RacingCoachException):
    """Base exception for validation errors."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, status_code=400)


class ConflictError(RacingCoachException):
    """Base exception for conflict errors (e.g., duplicate resource)."""

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message, status_code=409)
