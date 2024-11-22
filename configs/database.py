import sys
from pathlib import Path

from pydantic import Field

from configs.base import BaseConfig

sys.path.append(str(Path(__file__).parent.parent))


class PostgresDataBaseConfigs(BaseConfig):
    postgres_driver: str = Field(default="postgresql+asyncpg", validation_alias="MAIN_POSTGRES_DRIVER")
    postgres_user: str = Field(default="postgres", validation_alias="MAIN_POSTGRES_USER")
    postgres_password: str = Field(default="1234", validation_alias="MAIN_POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", validation_alias="MAIN_POSTGRES_HOST")
    postgres_port: str = Field(default="5000", validation_alias="MAIN_POSTGRES_PORT")
    postgres_database: str = Field(default="cusdever_client", validation_alias="MAIN_POSTGRES_DATABASE")

    @property
    def async_postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

    @property
    def sync_postgres_url(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"


class PostgresTestDataBaseConfigs(BaseConfig):
    test_postgres_driver: str = Field(default="postgresql+asyncpg", validation_alias="TEST_POSTGRES_DRIVER")
    test_postgres_user: str = Field(default="postgres", validation_alias="TEST_POSTGRES_USER")
    test_postgres_password: str = Field(default="1234", validation_alias="TEST_POSTGRES_PASSWORD")
    test_postgres_host: str = Field(default="localhost", validation_alias="TEST_POSTGRES_HOST")
    test_postgres_port: str = Field(default="5000", validation_alias="TEST_POSTGRES_PORT")
    test_postgres_database: str = Field(default="test_cusdever_client", validation_alias="TEST_POSTGRES_DATABASE")

    @property
    def async_postgres_url(self) -> str:
        return f"postgresql+asyncpg://{self.test_postgres_user}:{self.test_postgres_password}@{self.test_postgres_host}:{self.test_postgres_port}/{self.test_postgres_database}"

    @property
    def sync_postgres_url(self) -> str:
        return f"postgresql+psycopg2://{self.test_postgres_user}:{self.test_postgres_password}@{self.test_postgres_host}:{self.test_postgres_port}/{self.test_postgres_database}"


database_postgres_settings = PostgresDataBaseConfigs()
test_database_postgres_settings = PostgresTestDataBaseConfigs()
