import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from nats.js.api import DeliverPolicy
from nats.js.api import RetentionPolicy
from nats.js.api import StorageType
from pydantic import Field
from pydantic import field_validator

from configs.base import BaseConfig

sys.path.append(str(Path(__file__).parent.parent))


class NATSConfigs(BaseConfig):
    class RPCConfigs(BaseConfig):
        max_retries: int = Field(10, validation_alias='NATS_RPC_MAX_RETRIES')
        timeout: float = Field(10.0, validation_alias='NATS_RPC_TIMEOUT')

        @field_validator("timeout",
                         mode='before')
        def split_str(cls, field_data):
            if isinstance(field_data, int) or isinstance(field_data, str):
                return float(field_data)
            return field_data

    port: str = Field('4222', validation_alias='NATS_PORT')
    host: Optional[str] = Field('localhost', validation_alias='NATS_HOST')
    rpc: RPCConfigs = Field(default_factory=RPCConfigs)

    @property
    def nats_server_url(self) -> str:
        return f"nats://{self.host}:{self.port}"


class NATSCommunicatorSubscriber(BaseConfig):
    class CommandsQueues(BaseConfig):
        start_dialog: str = Field("command.dialog.start", validation_alias='COMMUNICATOR_QUEUE_COMMANDS_START_DIALOG')
        ping_user: str = Field("command.user.ping", validation_alias='COMMUNICATOR_QUEUE_COMMANDS_PING_USER')

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
            retention_policy: Enum = RetentionPolicy.WORK_QUEUE
            storage_type: Enum = StorageType.FILE
            deliver_policy: Enum = DeliverPolicy.ALL
            allow_direct: bool = True
            no_ack: bool = True

            stream: str = Field("DELAY_MESSAGE_SEND_STREEM", validation_alias='DISTRIBUTOR_FIRST_MESSAGE_STREEM')
            subject: str = Field("distribute.client.message.send.delay",
                                 validation_alias='DISTRIBUTOR_CLIENT_SEND_DELAY_MESSAGE')

        class MessageSend(BaseConfig):
            retention_policy: Enum = RetentionPolicy.WORK_QUEUE
            storage_type: Enum = StorageType.FILE
            deliver_policy: Enum = DeliverPolicy.ALL
            allow_direct: bool = True
            no_ack: bool = True

            stream: str = Field("SEND_MESSAGE_STREEM", validation_alias='DISTRIBUTOR_CONVERSATION_STREEM')
            subject: str = Field("distribute.client.message.send",
                                 validation_alias='DISTRIBUTOR_CLIENT_SEND_MESSAGE')

        first_message_message: FirstMessage = Field(default_factory=FirstMessage)
        send_message: MessageSend = Field(default_factory=MessageSend)

    class Parse(BaseConfig):
        class TelegramUserBaseInfo(BaseConfig):
            subject: str = Field("distribute.client.parse.info.base.many",
                                 validation_alias='DISTRIBUTOR_PARSER_GATHER_INFO')

        base_info: TelegramUserBaseInfo = Field(default_factory=TelegramUserBaseInfo)

    class Client(BaseConfig):
        create_new_client: str = Field("distribute.client.create",
                                       validation_alias='DISTRIBUTOR_CLIENT_CREATE')

    class Research: pass

    message: Message = Field(default_factory=Message)
    parser: Parse = Field(default_factory=Parse)
    client: Client = Field(default_factory=Client)


nast_base_settings = NATSConfigs()
nats_subscriber_communicator_settings = NATSCommunicatorSubscriber()
nats_subscriber_researcher_settings = NATSResearchSubscriber()
nats_distributor_settings = NATSDistributor()
