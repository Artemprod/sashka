from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

from src.schemas.service.research import ResearchDTOGet
from src_v0.schemas.message import UserMessageDTO, AssistantMessageDTO
from src_v0.schemas.status import UserStatusDTO, UserStatusNameDTO, UserStatusNameDTOGet


class UserDTOQueue(BaseModel):
    tg_user_id: int
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
    status: str
    last_online_date: Optional[datetime]  # Можно оставить datetime, а не строку
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True
        # Преобразование даты в строку при сериализации
        json_encoders = {
            datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
        }


class UserDTOBase(BaseModel):
    name: Optional[str]
    tg_user_id: Optional[int]


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
    created_at: Optional[datetime] = datetime.now()

    class Config:
        from_attributes = True


class UserDTOFull(UserDTO):
    user_id: int

    class Config:
        from_attributes = True

    # DTO с отношениями


class UserDTORel(UserDTOFull):
    status: "UserStatusNameDTOGet"
    messages: List["UserMessageDTO"] = Field(default_factory=list)
    assistant_messages: List["AssistantMessageDTO"] = Field(default_factory=list)
    researches: List["ResearchDTOGet"] = Field(default_factory=list)

    class Config:
        from_attributes = True
