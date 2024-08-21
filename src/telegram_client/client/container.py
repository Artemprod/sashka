import asyncio
import pickle
import uuid

from pyrogram import Client

from src.dispatcher.communicators.reggestry import ConsoleCommunicator
from src.telegram_client.client.model import ClientConfigDTO
from src.database.database_t import DictDatabase
from src.telegram_client.client.app_manager import Manager
from src.database.connections.redis_connect import RedisClient
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
    """
    Класс для управления клиентами с использованием паттерна Singleton.
    """

    def __init__(self, database: DictDatabase, redis_client: RedisClient):
        self._database = database
        self._redis_client = redis_client
        self.managers = {}
        self.gather_loops()

    @property
    def database(self):
        return self._database

    @property
    def redis_client(self):
        return self._redis_client

    @database.setter
    def database(self, new_database):
        self._database = new_database

    @redis_client.setter
    def redis_client(self, new_redis_client):
        self._redis_client = new_redis_client


    async def create_client_connection(self, client_configs: ClientConfigDTO, communicator, routers: list):
        client = Client(**client_configs.to_dict())
        manager = Manager(client=client, communicator=communicator)

        # TODO Можно вынести в отдельный метод
        for router in routers:
            manager.include_router(router)
        asyncio.create_task(manager.run())

        # FIXME Вот тут нейминг измени подумай как
        name = str(uuid.uuid4())[:6]
        self.managers[name] = manager
        # TODO Вот тут сервисный слой для управления базой и репой
        self.database.save(name, manager)

    async def update_client_statuses(self):
        while True:
            data: dict = {}
            for name, manager in self.managers.items():
                name: str
                manager: Manager
                data[name] = {
                    "is_connected": manager.app.is_connected,
                    "is_authorized": manager.is_authorize_status,
                    "session": manager.session_string,
                    "is_banned": manager.is_banned

                }
            redis_connection = await self.redis_client.get_connection()
            await redis_connection.set("CONNECTIONS", pickle.dumps(data), ex=15)

            # TODO Удалить после тестов
            statuses_bytes = await self.redis_client.get_current_client_connections("CONNECTIONS")
            print(statuses_bytes)
            await asyncio.sleep(10)

    def get_client_by_name(self, name: str):
        manager: Manager = self.managers[name]
        return manager.app

    def stop_client(self, name: str):
        manager: Manager = self.managers.get(name)
        if manager:
            manager.app.stop()
            logger.info(f"Stopped client with name {name}")
        else:
            logger.warning(f"Client with name {name} not found")

    def restart_client(self, name: str):
        self.stop_client(name)
        manager = self.managers[name]
        asyncio.create_task(manager.run(communicator=ConsoleCommunicator()))
        logger.info(f"Restarted client with name {name}")

    def delete_client(self, name: str):
        manager = self.managers.pop(name, None)
        if manager:
            self.database.delete(name)
            logger.info(f"Deleted client with name {name}")

    def _load_managers_from_db(self):
        db_managers = self.database.get_all()
        for name, manager in db_managers.items():
            if name and manager not in self.managers:
                self.managers[name] = manager

    # Запуск при первом запуске системы запускаем всех клиентов которые находятся в оперативной памяти
    def gather_loops(self):
        self._load_managers_from_db()
        return asyncio.gather(
            *[manager.run(communicator=ConsoleCommunicator()) for manager in self.managers.values() if manager],
            self.update_client_statuses(),
        )
