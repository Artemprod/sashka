class ParseError(Exception):
    def __init__(self, msg=None):
        self.msg = msg


class NoUserWithNameError(ParseError):
    def __repr__(self):
        return f"There is no user with name  {self.msg}"
