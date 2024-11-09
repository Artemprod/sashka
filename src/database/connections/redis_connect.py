import pickle

import redis.asyncio as redis

# TODO разделить на разные классы

# TODO Загружать сюда url из env
class RedisClient:
    REDIS_URL = f'redis://{"localhost"}:{6379}/{1}'

    def __init__(self, settings=None):
        self._settings = settings

    async def get_connection(self):
        if not self._settings:
            return redis.from_url(self.REDIS_URL, decode_responses=False)
        else:
            return redis.from_url(self._settings.redis_url)

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


class RedisCash(RedisClient):
    REDIS_URL = f'redis://{"localhost"}:{6379}/{2}'

    async def get_research_data(self, research):
        redis_connection = await self.get_connection()
        research_data = await redis_connection.get(research)
        if not research_data:
            return None
        return pickle.loads(research_data)

    async def update_data_in_cash(self, research, data: dict):
        redis_connection = await self.get_connection()
        await redis_connection.set(research, pickle.dumps(data))


class RedisPing(RedisClient):

    REDIS_URL = f'redis://{"localhost"}:{6379}/{3}'

    async def get_ping_status(self, user_id):
        redis_connection = await self.get_connection()
        ping_status = await redis_connection.get(user_id)

        if not ping_status:
            data = {"first": False, "second": False, "last": False}
            await redis_connection.set(user_id, pickle.dumps(data))
            ping_status = pickle.dumps(data)  # Update ping_status directly

        return pickle.loads(ping_status)

    async def update_ping_status(self, user_id, data: dict):
        redis_connection = await self.get_connection()
        await redis_connection.set(user_id, pickle.dumps(data))
