class MessageError(Exception):
    def __init__(self, msg=None):
        self.msg = msg


class FirstSendMessageError(MessageError):
    def __repr__(self):
        return f"Cant send first message   {self.msg}"

