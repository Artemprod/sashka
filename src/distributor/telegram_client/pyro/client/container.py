import asyncio
import datetime
import pickle
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pyrogram
from loguru import logger
from pyrogram import Client

from src.database.connections.redis_connect import RedisClient
from src.database.exceptions.read import EmptyTableError
from src.database.repository.storage import RepoStorage
from src.distributor.telegram_client.interface.container import InterfaceClientsContainer
from src.distributor.telegram_client.pyro.client.app_manager import Manager
from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.client import TelegramClientDTOPost


class ClientsManager(InterfaceClientsContainer):
    """Class for managing clients using the Singleton pattern."""
    MAX_ATTEMPTS = 35
    DELAY_BETWEEN_ATTEMPTS = 2
    MAX_TIMEOUT = 120

    def __init__(self, repository: RepoStorage,
                 redis_connection_manager: Optional[RedisClient],
                 dev_mode,
                 settings=None,
                 routers: List[Any] = None):

        self._repository = repository
        self._redis_connection_manager = redis_connection_manager
        self._routers = routers or []
        self.managers: Dict[str, Manager] = {}
        self.dev_mode = dev_mode
        self.settings = settings if settings else self._load_settings()

        logger.warning("DEV MODE IS ON") if self.dev_mode else logger.warning("PRODUCTION MODE")

    @property
    def repository(self) -> RepoStorage:
        return self._repository

    @repository.setter
    def repository(self, new_repository: RepoStorage):
        self._repository = new_repository

    @property
    def routers(self) -> List[Any]:
        return self._routers

    @routers.setter
    def routers(self, new_routers: List[Any]):
        self._routers = new_routers

    @property
    def redis_client(self) -> RedisClient:
        return self._redis_connection_manager

    @redis_client.setter
    def redis_client(self, new_redis_connection_manager: RedisClient):
        self._redis_connection_manager = new_redis_connection_manager

    @staticmethod
    def _load_settings():
        return {
            "shelve_file_name": "managers"
        }

    def add_router(self, new_router: Any):
        self._routers.append(new_router)

    async def create_client(self, client_configs: ClientConfigDTO, communicator) -> None:
        """Create a client connection and save its data."""
        client = Client(**client_configs.dict())
        manager = Manager(client=client, communicator=communicator, dev_mode=self.dev_mode)

        if self._routers:
            self.include_routers(manager, self._routers)
        else:
            logger.warning("No routers for client")

        self.managers[client_configs.name] = manager
        task = asyncio.create_task(manager.run())

        try:
            client_data = await asyncio.wait_for(self._wait_data(task, manager), timeout=ClientsManager.MAX_TIMEOUT)
            if client_data:
                await self._save_new_client(client_configs, manager, client_data)
                if self.dev_mode:
                    self._dev_mode_save_object_in_file(manager_object=manager)
            return
        except TimeoutError as te:
            logger.error(f"Timeout waiting for client data: {te}")

        except Exception as exc:
            logger.error(f"An error occurred during client connection: {exc}")
            task.cancel()

    @staticmethod
    async def _wait_data(task, manager: Manager) -> Optional['User']:
        """Wait for client data."""

        async def async_attempts():
            for attempt in range(1, ClientsManager.MAX_ATTEMPTS + 1):
                yield attempt
                await asyncio.sleep(ClientsManager.DELAY_BETWEEN_ATTEMPTS)

        async for attempt in async_attempts():
            try:
                if task.done():
                    result = await task
                    if isinstance(result, Exception):
                        logger.info(f"Break due to exception {result}")
                        break

                app = await manager.get_app()
                if app.me:
                    logger.info(f"User data received: {app.me}")
                    return app.me

                logger.info(f"Attempt {attempt}/{ClientsManager.MAX_ATTEMPTS}: Waiting for user data...")
            except asyncio.CancelledError:
                logger.info("Task was cancelled.")
                break

        raise TimeoutError("Failed to receive user data after maximum attempts")

    async def _save_new_client(self, configs: ClientConfigDTO, manager: Manager, client_data: 'User') -> Optional[
        TelegramClientDTOGet]:
        """Save a new client."""
        if manager.is_authorize_status and manager.session_string:
            parse_mode = configs.parse_mode.value if isinstance(configs.parse_mode,
                                                                pyrogram.enums.ParseMode) else configs.parse_mode
            client_dto = TelegramClientDTOPost(
                telegram_client_id=client_data.id,
                name=configs.name,
                api_id=str(configs.api_id),
                api_hash=str(configs.api_hash),
                app_version=configs.app_version,
                device_model=configs.device_model,
                system_version=configs.system_version,
                lang_code=configs.lang_code,
                test_mode=configs.test_mode,
                session_string=manager.session_string,
                phone_number=configs.phone_number,
                password=configs.password,
                parse_mode=parse_mode,
                workdir=configs.workdir,
                created_at=datetime.datetime.now()
            )
            try:
                new_client = await self.repository.client_repo.save(values=client_dto.dict())
                logger.info(f"New client saved: {client_dto.name}")
                return new_client
            except Exception as e:
                logger.error(f"Error saving client: {e}")
                raise

    def _dev_mode_save_object_in_file(self, manager_object: Manager):
        import shelve
        with shelve.open(self.settings.get('shelve_file_name', None)) as db:
            try:
                db[manager_object.app.name] = manager_object
                logger.info("Save manager object in file DEV MODE")
            except Exception as e:
                raise e

    @staticmethod
    def include_routers(manager: Manager, routers: List[Any]):
        """Include routers in the manager."""
        for router in routers:
            manager.include_router(router)

    async def update_client_statuses(self):
        """Update client connection statuses periodically."""
        while True:
            data = {
                name: {
                    "is_connected": manager.app.is_connected,
                    "is_authorized": manager.is_authorize_status,
                    "session": manager.session_string,
                    "is_banned": manager.is_banned
                }
                for name, manager in self.managers.items()
            }
            redis_connection = await self._redis_connection_manager.get_connection()
            await redis_connection.set("CONNECTIONS", pickle.dumps(data), ex=15)
            logger.debug(f"Client statuses updated in Redis: {data}")
            await asyncio.sleep(10)

    def get_client_manager_by_name(self, name: str) -> Optional[Any]:
        """Retrieve a client by its name."""
        manager = self.managers.get(name)
        if manager:
            return manager.app
        logger.warning(f"Client with name {name} not found")
        return None

    def stop_client(self, name: str):
        """Stop a client by its name."""
        manager = self.managers.get(name)
        if manager:
            manager.app.stop()
            logger.info(f"Stopped client with name {name}")
        else:
            logger.warning(f"Client with name {name} not found")

    def restart_client(self, name: str):
        """Restart a client by its name."""
        manager = self.managers.get(name)
        if manager:
            self.stop_client(name)
            asyncio.create_task(manager.run())
            logger.info(f"Restarted client with name {name}")
        else:
            logger.warning(f"Client with name {name} not found")

    def delete_client(self, name: str):
        """Delete a client by its name."""
        manager = self.managers.pop(name, None)
        if manager:
            self._repository.client_repo.delete(name)
            logger.info(f"Deleted client with name {name}")
        else:
            logger.warning(f"Client with name {name} not found")
    #TODO Тут будет ошибка с коммуникатором нужнго переделать логику загрузки коммуникатора
    async def _load_managers_from_db(self):
        """Load managers from the database."""
        logger.info("Loading managers from database...")
        try:
            db_managers = await self._repository.client_repo.get_all()
            for client_model in db_managers:
                if client_model.name not in self.managers:
                    dto = ClientConfigDTO.model_validate(client_model, from_attributes=True)
                    client = Client(**dto.dict())
                    manager = Manager(client=client, communicator=...)
                    if self._routers:
                        self.include_routers(manager, self.routers)
                    else:
                        logger.warning("No routers for client")
                    self.managers[client.name] = manager
            logger.info("Managers loaded from database")
        except EmptyTableError:
            logger.info("Client Table is empty")

    async def start_all_clients(self):
        """Start all loaded managers."""
        await self._load_managers_from_db()
        return asyncio.gather(
            *[manager.run() for manager in self.managers.values() if manager]
        )

    # def gather_loops(self):
    #     return asyncio.gather(*[manager.run() for manager in self.managers.values() if manager],
    #                           self.update_client_statuses(),
    #                           )
