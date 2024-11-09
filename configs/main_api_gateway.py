import sys
from pydantic import Field, field_validator

from configs.base import BaseConfig
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


class MainAPIBaseConfig(BaseConfig):
    host: str = Field("localhost", validation_alias='API_MAIN_UVICORN_HOST')
    port: int = Field(9194, validation_alias='API_MAIN_UVICORN_PORT')
    reload: str = Field(True, validation_alias='API_MAIN_RELOAD')
    lifespan: str = Field("on", validation_alias='API_MAIN_LIFESPAN')
    log_level: str = Field("debug", validation_alias='API_MAIN_LOG_LEVEL')

    @field_validator("reload",
                     mode='before')
    def is_reload(cls, field_data):
        if isinstance(field_data, str):
            return "true" == field_data.lower()
        return field_data
