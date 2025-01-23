import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field

from configs.base import BaseConfig

load_dotenv()
sys.path.append(str(Path(__file__).parent.parent))


class PostgresDataBaseConfigs(BaseConfig):
    postgres_driver: str = Field(default="postgresql+asyncpg", validation_alias="MAIN_POSTGRES_DRIVER")
    postgres_user: str = Field(default="postgres", validation_alias="MAIN_POSTGRES_USER")
    postgres_password: str = Field(default="1234", validation_alias="MAIN_POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", validation_alias="MAIN_POSTGRES_HOST")
    postgres_port: str = Field(default="5432", validation_alias="MAIN_POSTGRES_PORT")
    postgres_database: str = Field(default="cusdever_client", validation_alias="MAIN_POSTGRES_DATABASE")

    @property
    def async_postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

    @property
    def async_postgres_url_test(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}_test"

    @property
    def sync_postgres_url(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"


database_postgres_settings = PostgresDataBaseConfigs()
