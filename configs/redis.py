from pydantic import Field
from configs.base import BaseConfig
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

class RedisConfigs(BaseConfig):
    host: str = Field(default="localhost", validation_alias='REDIS_HOST')
    port: str = Field(default="6379", validation_alias='REDIS_PORT')

    @property
    def redis_url(self) -> str:
        return f"redis://{self.host}:{self.port}"


class RedisCashConfigs(RedisConfigs):
    database: int = Field(default=1, validation_alias='REDIS_CASH_DB2')

    @property
    def redis_url(self) -> str:
        return f"{super().redis_url}/{self.database}"


class RedisTelegramGetterConfigs(RedisConfigs):
    database: int = Field(default=10, validation_alias='REDIS_TELEGRAM_GETTER_DB')

    @property
    def redis_url(self) -> str:
        return f"{super().redis_url}/{self.database}"


redis_base_configs = RedisConfigs()
telegram_redis_getter_config = RedisTelegramGetterConfigs()
redis_cache_config = RedisCashConfigs()

