import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings

from configs.base import BaseConfig


class NATS(BaseConfig):
    port: str = Field('4222', validation_alias='NATS_PORT')
    host: Optional[str] = Field('localhost', validation_alias='NATS_HOST')

    @property
    def nats_server_url(self) -> str:
        return f"nats://{self.host}:{self.port}"


class NATSCommunicatorSubscriber(BaseConfig):
    class CommandsQueues(BaseConfig):
        start_dialog: str = Field("command.dialog.start", validation_alias='COMMUNICATOR_QUEUE_COMMANDS_START_DIALOG')

    class MessageQueues(BaseConfig):
        new_message: str = Field("message.income.new", validation_alias='COMMUNICATOR_QUEUE_MESAGES_NEW_INCOME_MESSAGE')

    commands: CommandsQueues = Field(default_factory=CommandsQueues)
    messages: MessageQueues = Field(default_factory=MessageQueues)


class NATSResearchSubscriber(BaseConfig):
    class ResearchQueues(BaseConfig):
        start_telegram_research: str = Field("research.telegram.start",
                                             validation_alias='RESEARCH_QUEUE_RESERACH_TELEGRAM_START')

    researches: ResearchQueues = Field(default_factory=ResearchQueues)


class NATSDistributor(BaseConfig):
    class Message(BaseConfig):
        class FirstMessage(BaseConfig):
            stream: str = Field("DELAY_MESSAGE_SEND_STREEM", validation_alias='DISTRIBUTOR_FIRST_MESSAGE_STREEM')
            subject: str = Field("distribute.client.message.send.delay",
                                 validation_alias='DISTRIBUTOR_CLIENT_SEND_DELAY_MESSAGE')

        class MessageSend(BaseConfig):
            stream: str = Field("SEND_MESSAGE_STREEM", validation_alias='DISTRIBUTOR_CONVERSATION_STREEM')
            subject: str = Field("distribute.client.message.send",
                                 validation_alias='DISTRIBUTOR_CLIENT_SEND_MESSAGE')

        first_message_message: FirstMessage = Field(default_factory=FirstMessage)
        send_message: MessageSend = Field(default_factory=MessageSend)

    class Parse(BaseConfig):
        class TelegramUserBaseInfo:
            subject: str = Field("distribute.client.parse.info.base.many",
                                 validation_alias='DISTRIBUTOR_PARSER_GATHER_INFO')

    class Client(BaseConfig):
        subject: str = Field("distribute.client.create",
                             validation_alias='DISTRIBUTOR_CLIENT_CREATE')

    class Research: pass

    message: Message = Field(default_factory=Message)
    parser: Parse = Field(default_factory=Parse)
    client: Client = Field(default_factory=Client)


n = NATSDistributor()
print(n.message.first_message_message.stream)
