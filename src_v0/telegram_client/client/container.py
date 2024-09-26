import asyncio
import datetime
import pickle
import uuid
from dataclasses import Field
from typing import Dict, Any

import pyrogram
from faststream.nats import NatsBroker
from pyrogram import Client

from src_v0.database.repository.storage import RepoStorage
from src_v0.dispatcher.communicators.reggestry import ConsoleCommunicator
from src_v0.telegram_client.client.model import ClientConfigDTO
from src_v0.database.database_t import DictDatabase
from src_v0.telegram_client.client.app_manager import Manager
from src_v0.database.connections.redis_connect import RedisClient
from loguru import logger


class SingletonMeta(type):
    """
    Метакласс для реализации паттерна Singleton.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


# DONE добавить загрузку сесси в редис
# DONE добавить проверку на вторизирва в редис и менеджер
# DONE вынести методы в редис клиент
# DONE добавить возможность мсменить базу данных на лету (сеттер)
# DONE добавить возможность получить необъодимые атрибуты через проепертя
# DONE Добавить методы получения работающего клиента
# DONE Вынести коммуникатор в инициализацию менеджера и передавть в create_client_connection
# TODO Нейминг клиентов и дополниетельные данные о них
# TODO Добавить перезаход для тех кто выкинулся из авторизации и удалить забаненых
# TODO Добавить автоматическое обновление статуса в базе данных


class ClientsManager(metaclass=SingletonMeta):
    """Класс для управления клиентами с использованием паттерна Singleton."""

    def __init__(self, repository: RepoStorage, redis_connection_manager: RedisClient, routers: list = None):
        self._repository = repository
        self._redis_connection_manager = redis_connection_manager
        self._routers = routers
        self.managers: Dict[str, Manager] = {}
        # self.gather_loops


    @property
    def repository(self) -> RepoStorage:
        return self._repository

    @property
    def routers(self) -> list:
        return self._routers

    @property
    def redis_client(self) -> RedisClient:
        return self._redis_connection_manager

    @routers.setter
    def routers(self, new_routers: list):
        self._routers = new_routers

    @repository.setter
    def repository(self, new_repository: RepoStorage):
        self._repository = new_repository

    @redis_client.setter
    def redis_client(self, new_redis_connection_manager: RedisClient):
        self._redis_connection_manager = new_redis_connection_manager

    def add_router(self, new_router):
        self._routers.append(new_router)

    async def create_client_connection(self, client_configs: ClientConfigDTO, communicator: Any, ):
        client = Client(**client_configs.dict())
        manager = Manager(client=client, communicator=communicator)
        if self._routers:
            self.include_routers(manager, self.routers)
        else:
            print("No routers for client")
        asyncio.create_task(manager.run())
        self.managers[client_configs.name] = manager


    def include_routers(self, manager: Manager, routers: list):
        for router in routers:
            manager.include_router(router)

    async def update_client_statuses(self):
        while True:
            data = {}
            for name, manager in self.managers.items():
                data[name] = {
                    "is_connected": manager.app.is_connected,
                    "is_authorized": manager.is_authorize_status,
                    "session": manager.session_string,
                    "is_banned": manager.is_banned
                }

            redis_connection = await self._redis_connection_manager.get_connection()
            await redis_connection.set("CONNECTIONS", pickle.dumps(data), ex=15)
            logger.debug(f"Client statuses updated in Redis: {data}")
            await asyncio.sleep(10)

    def get_client_by_name(self, name: str) -> Any:
        manager = self.managers.get(name)
        if manager:
            return manager.app
        logger.warning(f"Client with name {name} not found")
        return None

    def stop_client(self, name: str):
        manager = self.managers.get(name)
        if manager:
            manager.app.stop()
            logger.info(f"Stopped client with name {name}")
        else:
            logger.warning(f"Client with name {name} not found")

    def restart_client(self, name: str):
        manager = self.managers.get(name)
        if manager:
            self.stop_client(name)
            asyncio.create_task(manager.run())
            logger.info(f"Restarted client with name {name}")
        else:
            logger.warning(f"Client with name {name} not found")

    def delete_client(self, name: str):
        manager = self.managers.pop(name, None)
        if manager:
            self._repository.client_repo.delete(name)
            logger.info(f"Deleted client with name {name}")
        else:
            logger.warning(f"Client with name {name} not found")

    # TODO сделать загрузку из базы имеющихся клиентов
    async def _load_managers_from_db(self):
        logger.info("loading data ...")
        db_managers = await self._repository.client_repo.get_all()
        for client_model in db_managers:
            if client_model.name not in self.managers:
                dto = ClientConfigDTO.model_validate(client_model, from_attributes=True)
                print()
                client = Client(**dto.dict())
                manager = Manager(client=client, communicator=ConsoleCommunicator())
                if self._routers:
                    self.include_routers(manager, self.routers)
                else:
                    print("No routers for client")
                self.managers[client.name] = manager
        logger.info("Managers loaded from database")

    async def start(self):
        print()
        await self._load_managers_from_db()
        return asyncio.gather(*[manager.run() for manager in self.managers.values() if manager],
                              self.update_client_statuses(),
                              )
    # def gather_loops(self):
    #     return asyncio.gather(*[manager.run() for manager in self.managers.values() if manager],
    #                           self.update_client_statuses(),
    #                           )

