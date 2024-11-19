class ResearchErrors(Exception):
    def __init__(self, msg=None):
        self.msg = msg


class EmptyUniqueNamesForNewResearchError(ResearchErrors):
    def __repr__(self):
        return f"No unique username  {self.msg}"
