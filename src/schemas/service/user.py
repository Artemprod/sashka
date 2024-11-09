from datetime import datetime
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


# Общая конфигурация для сериализации datetime объектов
class ConfigBase:
    from_attributes = True
    json_encoders = {
        datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None
    }


# Базовый класс DTO
class UserDTOBase(BaseModel):
    username: Optional[str] = None
    tg_user_id: Optional[int] = None

    class Config(ConfigBase):
        pass


# Класс, представляющий очередь пользователей
class UserDTOQueue(BaseModel):
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
    status: str
    last_online_date: Optional[datetime] = None  # Можно оставить как datetime
    phone_number: Optional[str] = None

    class Config(ConfigBase):
        pass


# Расширенный класс DTO с дополнительными полями
class UserDTO(UserDTOBase):


    second_name: Optional[str] = None
    phone_number: Optional[str] = None
    tg_link: Optional[str] = None
    is_verified: Optional[bool] = None
    is_scam: Optional[bool] = None
    is_fake: Optional[bool] = None
    is_premium: Optional[bool] = None
    last_online_date: Optional[datetime] = None
    language_code: Optional[str] = None
    is_info: Optional[bool] = False
    created_at: Optional[datetime] = datetime.now()

    class Config(ConfigBase):
        pass


# Полный класс DTO, включающий user_id
class UserDTOFull(UserDTO):
    user_id: int

    class Config(ConfigBase):
        pass

class UserDTQueue(BaseModel):
    name: str
    tg_user_id: str

# DTO с отношениями между объектами
class UserDTORel(UserDTOFull):
    status: "UserStatusNameDTOGet"
    messages: List["UserMessageDTO"] = Field(default_factory=list)
    assistant_messages: List["AssistantMessageDTO"] = Field(default_factory=list)
    researches: List["ResearchDTOGet"] = Field(default_factory=list)

    class Config(ConfigBase):
        pass
