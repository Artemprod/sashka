import sys
from pathlib import Path

from pydantic import Field

from configs.base import BaseConfig
from dotenv import load_dotenv
load_dotenv()

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

class RedisApschedulerConfigs(RedisConfigs):

    research_start_database: int = Field(default=12, validation_alias='REDIS_APSCHEDULER_RESEARCH_START')
    first_message_database: int = Field(default=13, validation_alias='REDIS_APSCHEDULER_FIRST_MESSAGE')
    inspector_database: int = Field(default=14, validation_alias='REDIS_APSCHEDULER_INSPECTOR')

    jobs_key:str = 'apscheduler.jobs'
    run_times_key:str = 'apscheduler.run_times'

    @property
    def redis_url(self) -> str:
        return f"{super().redis_url}/{self.database}"

redis_base_configs = RedisConfigs()
telegram_redis_getter_config = RedisTelegramGetterConfigs()
redis_cache_config = RedisCashConfigs()
redis_apscheduler_config = RedisApschedulerConfigs()

