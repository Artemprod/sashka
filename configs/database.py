import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings

from configs.base import BaseConfig


# load_dotenv()

class PostgresDataBaseConfigs(BaseConfig):
    postgres_driver: str = Field(default="postgresql+asyncpg", env="MAIN_POSTGRES_DRIVER")
    postgres_user: str = Field(default="postgres", env="MAIN_POSTGRES_USER")
    postgres_password: str = Field(default="1234", env="MAIN_POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", env="MAIN_POSTGRES_HOST")
    postgres_port: str = Field(default="5432", env="MAIN_POSTGRES_PORT")
    postgres_database: str = Field(default="cusdever_client", env="MAIN_POSTGRES_DATABASE")

    @property
    def async_postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

    @property
    def sync_postgres_url(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"