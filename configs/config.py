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

class NATS(BaseConfig):
    nats_port: str = Field('4222', env='NATS_PORT')
    nats_host: Optional[str] = Field('localhost', env='NATS_HOST')

    @property
    def nats_server_url(self) -> str:
        return f"nats://{self.nats_host}:{self.nats_port}"


class NATSCommunicatorSubscriber(NATS):
    class CommandsQueues(BaseConfig):
        # prefix: str = Field("command", validation_alias='COMMUNICATOR_QUEUE_COMMANDS_PREFIX')

        class Dialog(BaseConfig):
            # start: str = Field("dialog.start", validation_alias='COMMUNICATOR_QUEUES_COMMANDS_DIALOG_START')

            @property
            def dialog_start_command(self) -> str:
                return self.start

        dialog: Dialog = Field(default_factory=Dialog)

        @property
        def dialog_queue(self) -> Dialog:
            return self.dialog

    class MessageQueues(BaseConfig):
        # prefix: str = "message"

        class Income(BaseConfig):
            income: str = Field("income.new", validation_alias="INCOME")

            @property
            def message_income_new(self) -> str:
                return self.income

        income: Income = Field(default_factory=Income)

        @property
        def income_queue(self) -> Income:
            return self.income

    commands: CommandsQueues = Field(default_factory=CommandsQueues)
    message: MessageQueues = Field(default_factory=MessageQueues)

    @property
    def dialog_start_queue(self) -> str:
        return f"{self.commands.prefix}.{self.commands.dialog_queue.dialog_start_command}"

    @property
    def message_new_queue(self) -> str:
        return f"{self.message.prefix}.{self.message.income_queue.income}"





