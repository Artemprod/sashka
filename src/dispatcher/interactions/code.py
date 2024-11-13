from redis.asyncio import Redis
from environs import Env
from environs import EnvError
from loguru import logger

from configs.redis import RedisTelegramGetterConfigs
from src.dispatcher.models import DataType


class CodeGetter: pass


class TelegramGetter(CodeGetter): pass


# TODO задасть таймауты и отсальные конфиги в ENV
class RedisTelegramGetter:
    BASE_TIMEOUT = 60 * 5  # Базовый тайм-аут ожидания данных в секундах
    BASE_TABLE_NAME = 'telegram'
    REDIS_URL = 'redis://"localhost":6379/10'

    def __init__(self, settings: RedisTelegramGetterConfigs = None):
        self.settings = settings
        self._redis_url = self._load_redis_url()

    def _load_redis_url(self) -> str:
        if not self.settings:
            logger.warning("No settings load from env")
            env = Env()
            env.read_env('.env')
            try:
                redis_url = env("REDIS_URL")
                logger.debug("Redis URL successfully loaded")
                return redis_url
            except EnvError as e:
                logger.error("Failed to load Redis URL from environment")
                raise e
        else:
            return self.settings.redis_url

    async def _wait_for_telegram_data(self, key: str) -> tuple:
        """Ожидает данные от Redis по указанному ключу."""
        async with Redis.from_url(self._redis_url) as redis:
            logger.info(f"Waiting for data on key '{key}' with timeout {self.BASE_TIMEOUT} seconds...")
            data = await redis.blpop(key, timeout=self.BASE_TIMEOUT)

            if data and data[1]:
                return data[0].decode('utf-8'), data[1].decode('utf-8')
            else:
                logger.warning(f"Timeout reached or no data received for key '{key}'")
                raise TimeoutError(f"No data received for key '{key}' within the timeout period")

    async def get_value_by_key(self, user_id: str, expected_key: str) -> str:
        """Извлекает значение из Redis по ключу, проверяя соответствие ожидаемому ключу."""
        key = f"{RedisTelegramGetter.BASE_TABLE_NAME}:{expected_key}:{user_id}"
        data = await self._wait_for_telegram_data(key)
        if expected_key in data[0].lower():
            return str(data[1])
        else:
            raise ValueError(f"Invalid key format: expected '{expected_key}' in key")

    # Методы для конкретных значений
    async def get_code(self, user_id: str) -> str:
        return await self.get_value_by_key(user_id, DataType.CODE.value)

    async def get_recovery_code(self, user_id: str) -> str:
        return await self.get_value_by_key(user_id, DataType.RECOVERY.value)

    async def get_phone_number(self, user_id: str) -> str:
        return await self.get_value_by_key(user_id, DataType.PHONE.value)

    async def get_cloud_password(self, user_id: str) -> str:
        return await self.get_value_by_key(user_id, DataType.CLOUD_PASSWORD.value)

    async def get_confirmation(self, user_id: str) -> str:
        return await self.get_value_by_key(user_id, DataType.CONFIRM.value)

    async def get_first_name(self, user_id: str) -> str:
        return await self.get_value_by_key(user_id, DataType.FIRST_NAME.value)

    async def get_last_name(self, user_id: str) -> str:
        return await self.get_value_by_key(user_id, DataType.LAST_NAME.value)
