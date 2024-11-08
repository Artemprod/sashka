import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings


load_dotenv()


class BaseConfig(BaseSettings):
    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# class UvicornServer(BaseConfig):
#     uvicorn_host: str = "0.0.0.0"
#
#
# class GPTConfigs(BaseConfig):
#     gpt_model_version: Optional[str] = '3.5-turbo'
#     gpt_model_temperature: Optional[float] = 1.00
#     context_length: Optional[int] = 1
#     gpt_max_return_tokens: Optional[int] = 1
#
#
# class OpenAiConfigs(BaseConfig):
#     openai_api_key: str = ''
#
#
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


class NATS(BaseConfig):
    nats_port: str = Field('4222', env='NATS_PORT')
    nats_host: Optional[str] = Field('localhost', env='NATS_HOST')

    @property
    def nats_server_url(self) -> str:
        return f"nats://{self.nats_host}:{self.nats_port}"


class NATSCommunicatorSubscriber(NATS):
    class CommandsQueues(BaseConfig):
        prefix: str = Field("command", env='COMMUNICATOR_QUEUE_COMMANDS_PREFIX')

        class Dialog(BaseConfig):
            start: str = Field("dialog.start", env='COMMUNICATOR_QUEUES_COMMANDS_DIALOG_START')

            @property
            def dialog_start_command(self) -> str:
                return self.start

        dialog: Dialog = Dialog()

        @property
        def dialog_queue(self) -> Dialog:
            return self.dialog

    class MessageQueues(BaseConfig):
        prefix: str = "message"

        class Income(BaseConfig):
            income: str = Field("income.new", env='COMMUNICATOR_QUEUES_COMMANDS_INCOME_NEW')

            @property
            def message_income_new(self) -> str:
                return self.income

        income: Income = Income()

        @property
        def income_queue(self) -> Income:
            return self.income

    commands: CommandsQueues = CommandsQueues()
    message: MessageQueues = MessageQueues()

    @property
    def dialog_start_queue(self) -> str:
        return f"{self.commands.prefix}.{self.commands.dialog_queue.dialog_start_command}"

    @property
    def message_new_queue(self) -> str:
        return f"{self.message.prefix}.{self.message.income_queue.income}"



class RedisConfigs(BaseConfig):
    redis_host: str = Field('localhost', env='REDIS_HOST')
    redis_port: str = Field('6379', env='REDIS_PORT')

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"


class RedisCash(RedisConfigs):
    redis_external_db: int = Field(1, env='REDIS_CASH_DB2')  # Использует int для обозначения базы данных

    @property
    def redis_url(self) -> str:
        return f"{super().redis_url}/{self.redis_external_db}"


class RedisTelegramGetter(RedisConfigs):
    redis_telegram_db: int = Field(10, env='REDIS_TELEGRAM_GETTER_DB')  # Использует int для обозначения базы данных

    @property
    def redis_url(self) -> str:
        return f"{super().redis_url}/{self.redis_telegram_db}"


# class SentryConfigs(BaseConfig):
#     sentry_dns_fast_api: str = ''
#     sentry_dns_worker: str = ''
#
#
# class ProjectSettings(BaseConfig):
#     language: str = 'ru'
#
#     uvicorn_server: UvicornServer = Field(default_factory=UvicornServer)
#     gpt: GPTConfigs = Field(default_factory=GPTConfigs)
#
#     openai: OpenAiConfigs = Field(default_factory=OpenAiConfigs)
#     postgres: PostgresDataBaseConfigs = Field(default_factory=PostgresDataBaseConfigs)
#
#     nats_publisher: NATSPublisherConfigs = Field(default_factory=NATSPublisherConfigs)
#     redis: RadisConfigs = Field(default_factory=RadisConfigs)
#
#     sentry: SentryConfigs = Field(default_factory=SentryConfigs)

# print(ProjectSettings())
# external_config = RedisExternalInteraction()
telegram_config = RedisTelegramGetter()

print(telegram_config.redis_url)
# print(nats_subscriber_config.message_new_queue)
# Для диагностики
print(f"NATS_PORT from env: {os.getenv('NATS_PORT')}")
print(f"COMMUNICATOR_QUEUE_COMMANDS_PREFIX from env: {os.getenv('NATS_POT')}")
print(f"COMMUNICATOR_QUEUES_COMMANDS_DIALOG_START from env: {os.getenv('COMMUNICATOR_QUEUES_COMMANDS_DIALOG_START')}")
print(f"COMMUNICATOR_QUEUES_COMMANDS_INCOME_NEW from env: {os.getenv('COMMUNICATOR_QUEUES_COMMANDS_INCOME_NEW')}")

# Пример использования
nats_subscriber_config = NATSCommunicatorSubscriber()
print(nats_subscriber_config.message_new_queue)
print(nats_subscriber_config.dialog_start_queue)