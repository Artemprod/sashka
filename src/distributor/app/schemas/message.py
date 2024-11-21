from datetime import datetime
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pyrogram import Client
from telethon import TelegramClient

from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer


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
    container: Union[ClientsManager,TelethonClientsContainer]
    current_time: datetime
    send_time: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class MessageToSendData(BaseModel):

    message:str
    user: UserDTOBase

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

Datas.model_rebuild()
