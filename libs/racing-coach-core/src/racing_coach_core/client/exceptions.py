class RacingCoachClientError(Exception):
    """Base exception for all Racing Coach client errors."""
    pass


class RequestError(RacingCoachClientError):
    """Raised when a request fails due to network or HTTP errors."""
    
    def __init__(self, message: str, status_code: int | None = None, response_text: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class ServerError(RacingCoachClientError):
    """Raised when the server returns an error response."""
    
    def __init__(self, message: str, status_code: int, response_data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data