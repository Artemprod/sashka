import os
from typing import Optional, List, Dict

from dotenv import load_dotenv
from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings

from configs.base import BaseConfig


class ResearchService(BaseConfig):
    ...
    # class RPCConfigs(BaseConfig):
    #     max_retries: int = Field(10, validation_alias='NATS_RPC_MAX_RETRIES')
    #     timeout: float = Field(10.0, validation_alias='NATS_RPC_TIMEOUT')
    #
    #     @field_validator("timeout",
    #                      mode='before')
    #     def split_str(cls, field_data):
    #         if isinstance(field_data, int) or isinstance(field_data, str):
    #             return float(field_data)
    #         return field_data
    #
    # port: str = Field('4222', validation_alias='NATS_PORT')
    # host: Optional[str] = Field('localhost', validation_alias='NATS_HOST')
    # rpc: RPCConfigs = Field(default_factory=RPCConfigs)
    #
    # @property
    # def nats_server_url(self) -> str:
    #     return f"nats://{self.host}:{self.port}"


class ResearchInspector(ResearchService):
    class CommandsQueues(BaseConfig):
        start_dialog: str = Field("command.dialog.start", validation_alias='COMMUNICATOR_QUEUE_COMMANDS_START_DIALOG')

    class MessageQueues(BaseConfig):
        new_message: str = Field("message.income.new", validation_alias='COMMUNICATOR_QUEUE_MESAGES_NEW_INCOME_MESSAGE')

    commands: CommandsQueues = Field(default_factory=CommandsQueues)
    messages: MessageQueues = Field(default_factory=MessageQueues)


class ResearchOvercChecker(ResearchService):
    delay_check_interval: int = Field(60, validation_alias='DELAY_BETWEEN_TIME_CHECKING_SECONDS')


class ResearchWordStopper(BaseConfig):
    base_words: List[str] = ["завершено", "исследование завершено", "конец исследования", "окончено", "STOP"]
    stop_words: List[str] = Field(
        default_factory=lambda: ResearchWordStopper.base_words.copy(),
        validation_alias='STOP_WORD_CHECKER_STOP_WORDS_LIST'
    )

    @field_validator("stop_words", mode='before')
    def split_str(cls, field_data):
        print()
        # Проверка, является ли значение строкой; если да, разделяем по запятой
        if isinstance(field_data, str):
            return field_data.split(',')
        return field_data


class ResearchPingator(BaseConfig):

    max_pings_messages: int = Field(default=4,
                                    validation_alias='PINGATOR_MAX_PINGS_MESSAGES')
    ping_attempts_multiplier: int = Field(default=2,
                                          validation_alias='PINGATOR_PING_ATTEMPT_MULTIPLIER')
    ping_interval: int = Field(default=10,
                               validation_alias='PINGATOR_PING_INTERVAL_CHEKING')


a = ResearchWordStopper()
print(type(a.stop_words))
