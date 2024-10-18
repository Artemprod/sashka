from typing import Optional
from datetime import datetime


from pydantic import BaseModel
from pyrogram import Client


from src.distributor.telegram_client.pyro.client.container import ClientsManager


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
    client: Client
    container: ClientsManager
    current_time: datetime
    send_time: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True