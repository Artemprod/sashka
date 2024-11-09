from abc import ABC
from abc import abstractmethod

from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO


class InterfaceClientsContainer(ABC):

    @abstractmethod
    async def create_client(self, client_configs: ClientConfigDTO, communicator):
        pass

    @abstractmethod
    def delete_client(self, name: str):
        pass

    @abstractmethod
    def get_client_manager_by_name(self, name: str):
        pass

    @abstractmethod
    async def _load_managers_from_db(self):
        pass

    @abstractmethod
    async def start_all_clients(self):
        pass
