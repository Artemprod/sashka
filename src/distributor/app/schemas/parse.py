from datetime import datetime
from typing import Optional, List, Union

from pydantic import BaseModel, Field
from pyrogram import Client
from telethon import TelegramClient

from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer


class UserDTOBase(BaseModel):
    username: Optional[str]
    tg_user_id: Optional[int]


class Datas(BaseModel):
    users: List[UserDTOBase] = Field(default_factory=list)
    client_name: str
    client: Optional[Union['Client', TelegramClient]]
    container: Optional[Union['ClientsManager', TelethonClientsContainer]]

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


Datas.model_rebuild()


class UserInfo(BaseModel):
    tg_user_id: int
    username:str
    is_contact: bool
    is_mutual_contact: bool
    is_deleted: bool
    is_bot: bool
    is_verified: bool
    is_restricted: bool
    is_scam: bool
    is_fake: bool
    is_support: bool
    is_premium: bool
    name: Optional[str] = None
    last_name: Optional[str] = None
    second_name: Optional[str] = None
    status: Optional[str] = None
    last_online_date: Optional[datetime]= Field(default=datetime.now())
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True
        # Преобразование даты в строку при сериализации
        json_encoders = {
            datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
        }


class TelegramClientDTO(BaseModel):

    client_id: int
    telegram_client_id: int
    name: str
    api_id: str
    api_hash: str
    app_version: str
    device_model: str
    system_version: str

    lang_code: Optional[str] = None
    test_mode: bool = False
    session_string: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    parse_mode: Optional[str] = 'html'
    workdir: Optional[str] = None
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True
