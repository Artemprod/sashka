class AttributeError(Exception):
    def __init__(self, msg=None):
        self.msg = msg


class UsernameError(AttributeError):
    def __repr__(self):
        return f"No username in DTO {self.msg}"
