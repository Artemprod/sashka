import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings

from configs.base import BaseConfig


class RedisConfigs(BaseConfig):
    host: str = Field(default="localhost", validation_alias='REDIS_HOST')
    port: str = Field(default="6379", validation_alias='REDIS_PORT')

    @property
    def redis_url(self) -> str:
        return f"redis://{self.host}:{self.port}"


class RedisCash(RedisConfigs):
    database: int = Field(default=1, validation_alias='REDIS_CASH_DB2')

    @property
    def redis_url(self) -> str:
        return f"{super().redis_url}/{self.database}"


class RedisTelegramGetter(RedisConfigs):
    database: int = Field(default=10, validation_alias='REDIS_TELEGRAM_GETTER_DB')

    @property
    def redis_url(self) -> str:
        return f"{super().redis_url}/{self.database}"


telegram_config = RedisTelegramGetter()

print(telegram_config.redis_url)