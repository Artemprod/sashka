from datetime import datetime
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pyrogram import Client
from telethon import TelegramClient

from src.distributor.services.ban_checker import ClientBanChecker
from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer
from src.services.publisher.publisher import NatsPublisher


class NatsHeaders(BaseModel):
    class Config:
        allow_population_by_field_name = True
        from_attributes = True


class UserDTOBase(BaseModel):
    name: Optional[str] = None
    tg_user_id: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class TelegramTimeDelaHeadersDTO(NatsHeaders):
    tg_client_name: str
    users: str
    send_time_msg_timestamp: str
    send_time_next_message_timestamp: str


class Datas(BaseModel):
    user: UserDTOBase
    client_name: str
    client: Union[Client, TelegramClient]
    container: Union[ClientsManager, TelethonClientsContainer]
    current_time: datetime
    send_time: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class MessageToSendData(BaseModel):
    message: str
    user: UserDTOBase

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


Datas.model_rebuild()


class MessageContext:
    def __init__(
            self,
            client: TelegramClient,
            publisher: NatsPublisher,
            research_id: Optional[int] = None,
            client_name: Optional[str] = None,
            client_ban_checker: Optional[ClientBanChecker] = None
    ):
        self.client = client
        self.publisher = publisher
        self.research_id = research_id
        self.client_name = client_name
        self.client_ban_checker = client_ban_checker
