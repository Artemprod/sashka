class ClientContainer:

    def __init__(self):
        self._clients = {}

    def add_client(self, client, name: str):
        self._clients[name] = client

    def get_client(self, name):
        return self._clients[name]

    @property
    def clients(self):
        return self._clients