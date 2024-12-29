class ExistenceError(Exception):
    def __init__(self, orm_object=None, msg=None):
        self.msg = msg
        self.orm_object = orm_object


class ObjectDoesNotExist(ExistenceError):
    def __repr__(self):
        return f"Object {self.orm_object} does not exist {self.msg}"


class EmptyTableError(ExistenceError):
    def __repr__(self):
        return f"There are not any objects in database.  {self.msg}"


class NoFreeClientsError(ExistenceError):
    def __repr__(self):
        return f"There are not any free clients for researches in database. All clients are busy"
