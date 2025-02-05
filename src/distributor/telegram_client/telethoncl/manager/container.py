import asyncio
from asyncio import CancelledError
from typing import Dict
from typing import List
from typing import Optional

from loguru import logger
from telethon import TelegramClient

from configs.clients import telethon_container_settings
from src.database.exceptions.read import EmptyTableError
from src.database.repository.storage import RepoStorage
from src.dispatcher.communicators.consol import ConsoleCommunicator
from src.distributor.telegram_client.interface.container import InterfaceClientsContainer
from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO
from src.distributor.telegram_client.telethoncl.manager.manager import TelethonManager
from src.services.exceptions.telegram_clients import AllClientsBannedError


class TelethonClientsContainer(InterfaceClientsContainer):
    def __init__(self, repository: RepoStorage, handlers: List = None):
        self.repository = repository
        self.handlers = handlers or []
        self.dev_mode = telethon_container_settings.def_mode
        self.settings = telethon_container_settings
        self.managers: Dict[str, TelethonManager] = {}
        self.loop = asyncio.get_event_loop()

        logger.warning("DEV MODE IS ON") if self.dev_mode else logger.warning("PRODUCTION MODE")

    def __getitem__(self, item: str):
        return self.managers[item]

    def __setitem__(self, key: str, value):
        self.managers[key] = value
        logger.info(f"Added {value}")

    def _load_settings(self):
        return {"shelve_file_name": "managers"}

    async def create_client(self, client_configs: ClientConfigDTO, communicator=ConsoleCommunicator()):
        try:
            manager = TelethonManager(self.repository, client_configs)
            manager.add_handlers(self.handlers)
            await manager.new_client(communicator)
            self.managers[client_configs.name] = manager
            logger.info(f"Client {client_configs.name} created and added to manager.")
            return client_configs.name
        except Exception as e:
            logger.error(f"Error creating client {client_configs.name}: {str(e)}")
            raise

    async def create_and_start_client(self, client_configs: ClientConfigDTO, communicator=ConsoleCommunicator()):
        try:
            client_name = await self.create_client(client_configs, communicator)
            logger.info("Mangager creaste client")
            await self.start_client(name=client_name)

        except Exception as e:
            logger.error(f"Error creating and starting client {client_configs.name}: {str(e)}")
            raise

    async def start_client(self, name: str):
        manager = self.managers.get(name)
        if manager and manager.saved_client:
            logger.info(f"Starting client {name}.")
            try:
                await manager.run()
            except Exception as e:
                logger.error(f"Error starting client {name}: {str(e)}")
        else:
            logger.warning(f"Manager for client {name} not found.")

    async def stop_client(self, name: str):
        manager = self.managers.get(name)
        if manager:
            logger.info(f"Stopping client {name}.")
            await manager.stop_client()
        else:
            logger.warning(f"Manager for client {name} not found.")

    def delete_client(self, name: str):
        if name in self.managers:
            del self.managers[name]
            logger.info(f"Deleted manager for client with name {name}.")
        else:
            logger.warning(f"Manager for client {name} not found.")

    def get_client_manager_by_name(self, name: str) -> Optional[TelethonManager]:
        return self.managers.get(name)

    def get_telethon_client_by_name(self, name: str) -> Optional[TelegramClient]:
        manager: TelethonManager = self.managers.get(name)
        return manager.run_strategy.client

    async def get_telethon_client_by_research_id(self, research_id: int) -> TelegramClient:
        """
        Возвращает первого не забаненного клиента для исследования
        """
        clients = await self.repository.client_repo.get_clients_by_research_id(
            research_id=research_id
        )
        logger.debug(f"Clients for research {research_id}: {clients}")
        logger.debug(f"Clients manager {self.managers.values()}")
        for client in clients:
            logger.debug(f"Client: {client.name} {client.is_banned}")
            if client.name in self.managers and not client.is_banned:
                manager: TelethonManager = self.managers.get(client.name)
                return manager.run_strategy.client

        raise AllClientsBannedError(
            f'All clients for research {research_id} are banned'
        )

    def get_client_manager_by_telegram_id(self, telegram_id: int) -> Optional[TelethonManager]:
        for manager in self.managers.values():
            if manager.saved_client and manager.saved_client.telegram_client_id == telegram_id:
                return manager
        logger.warning(f"Manager for Telegram ID {telegram_id} not found.")
        return None

    async def _load_managers_from_db(self):
        """Load managers from the database and prepare them for running."""
        logger.info("Loading managers from database...")
        try:
            db_managers = await self.repository.client_repo.get_all()
            for client_model in db_managers:
                if client_model.name not in self.managers:
                    dto = ClientConfigDTO.model_validate(client_model, from_attributes=True)
                    manager = TelethonManager(self.repository, dto)
                    manager.saved_client = client_model
                    manager.add_handlers(self.handlers)
                    self.managers[client_model.name] = manager
                    logger.info(f"Manager for client {client_model.name} initialized and added to managers collection.")
            logger.info("All managers loaded from database.")
        except EmptyTableError:
            logger.info("Client table is empty.")
        except Exception as e:
            logger.error(f"Error loading managers from the database: {str(e)}")

    async def start_all_clients(self):
        await self._load_managers_from_db()
        tasks = [self.start_client(name) for name in self.managers]
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in starting all clients: {str(e)}")
        except CancelledError:
            logger.info("Client start operation cancelled.")
