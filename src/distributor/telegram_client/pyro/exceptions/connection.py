class ConnectionError(Exception):
    pass


class ClientConnectionError(ConnectionError):
    """Exception raised when a client cant connect to telegram server."""

    def __init__(self, message=None):
        super().__init__(f"Client can't connect to server {message} ")


class NoClientError(ConnectionError):
    def __init__(self, message=None):
        super().__init__(f"No client {message} ")
