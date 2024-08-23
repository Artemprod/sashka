class ResponseError(Exception):
    pass


class NoResponseFromChatGptSError(ResponseError):
    def __init__(self, exception):
        self.exception = exception

        super().__init__(
            f"No response from Chat gpt API  {exception} "
        )
