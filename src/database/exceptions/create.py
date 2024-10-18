class CreationError(Exception):
    def __init__(self, orm_object, msg=None):
        self.msg = msg
        self.orm_object = orm_object


class ObjectWasNotCreated(CreationError):
    def __repr__(self):
        return f"Object {self.orm_object} was not created in database {self.msg }"
