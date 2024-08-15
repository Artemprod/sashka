class AuthorizationError(Exception):
    pass


class ClientAuthorizationConnectionError(AuthorizationError):
    """Exception raised when a client cant Authorize."""

    def __init__(self, message=None):
        super().__init__(
            f"Client can't Authorize {message} "
        )


class MaxAttemptsExceededError(AuthorizationError):
    """Exception raised when reach max auth try."""

    def __init__(self, message=None):
        super().__init__(
            f"Max auth try {message} "
        )
