import os
import pickle

import redis.asyncio as redis


# TODO Загружать сюда url из env
class RedisClient:
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 3

    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    async def get_connection(self):
        return redis.from_url(self.REDIS_URL, decode_responses=False)

    # TODO Добавить класс DTO для валидации и получения коннектов
    async def get_current_client_connections(self, connection_name: str):
        redis_connection = await self.get_connection()
        statuses_bytes = await redis_connection.get(connection_name)
        if statuses_bytes:
            # Десериализуем данные с помощью pickle
            statuses = pickle.loads(statuses_bytes)
            print(statuses)
            return statuses

    # TODO Добавить класс DTO для отдельного коннекта
    async def get_client_connection_info(self, connection_name, client_name: str):

        redis_connection = await self.get_connection()
        statuses_bytes = await redis_connection.get(connection_name)
        if statuses_bytes:
            # Десериализуем данные с помощью pickle
            clients = pickle.loads(statuses_bytes)
            print(clients)
            return clients[client_name]

    # async def get_authorized_client(self, connection_name, client_name: str):
    #
    #     redis_connection = await self.get_connection()
    #     statuses_bytes = await redis_connection.get(connection_name)
    #     if statuses_bytes:
    #         # Десериализуем данные с помощью pickle
    #         clients = pickle.loads(statuses_bytes)
    #         print(clients)
    #         return clients[client_name]


class RedisCash:
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 4

    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    async def get_connection(self):
        return redis.from_url(self.REDIS_URL, decode_responses=False)

    async def get_research_data(self, research):
        redis_connection = await self.get_connection()
        research_data = await redis_connection.get(research)
        if not research_data:
            return None
        return pickle.loads(research_data)

    async def update_data_in_cash(self, research, data:dict):
        redis_connection = await self.get_connection()
        await redis_connection.set(research, pickle.dumps(data))
