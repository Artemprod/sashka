import dataclasses


class IDatabase:

    def save(self, *args, **kwarg):
        ...

    def get(self, *args, **kwarg):
        ...


class DictDatabase(IDatabase):

    def __init__(self):
        self.data = {}

    def save(self, name, client):
        self.data[name] = client

    def get(self, name):
        return self.data[name]

    def delete(self, name):
        del self.data[name]

    def get_all(self):
        return self.data

class CommonDictDatabase(DictDatabase):
    def save(self, name, obj):
        self.data[name] = obj


database = DictDatabase()
comon_database = CommonDictDatabase()
