class ResearchErrors(Exception):
    def __init__(self, msg=None):
        self.msg = msg


class EmptyUniqueNamesForNewResearchError(ResearchErrors):
    def __repr__(self):
        return f"No unique username  {self.msg}"


class UntimelyCompletionError(ResearchErrors):
    def __repr__(self):
        return f"Method that complete research was called untimely {self.msg}"


class StatusError(ResearchErrors):
    def __repr__(self):
        return f"{self.msg}"


class ResearchCompletionError(ResearchErrors):
    def __repr__(self):
        return f"The research has been completed with error{self.msg}"


class UserInProgressError(ResearchCompletionError):
    pass


class ResearchStatusInProgressError(ResearchCompletionError):
    pass


class UserAndResearchInProgressError(ResearchCompletionError):
    pass
