class DataError(Exception):
    pass


class NoClientDataError(DataError):
    """Exception raised when no data."""

    def __init__(self, message=None):
        super().__init__(
            f"No client data to start {message} "
        )

