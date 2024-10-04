from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


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
        # Преобразование даты в строку при сериализации
        json_encoders = {
            datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
        }


class UserDTO(BaseModel):

    name: str
    second_name: Optional[str] = None
    phone_number: Optional[str] = None
    tg_user_id: int
    tg_link: Optional[str] = None
    is_verified: Optional[bool] = None
    is_scam: Optional[bool] = None
    is_fake: Optional[bool] = None
    is_premium: Optional[bool] = None
    last_online_date: Optional[datetime] = None
    language_code: Optional[str] = None
    created_at: Optional[datetime] = None


class UserDTOFull(UserDTO):
    user_id: int

    class Config:
        orm_mode = True


# DTO с отношениями
class UserDTORel(UserDTOFull):
    status: "UserStatusDTO"
    messages: List["UserMessageDTO"] = Field(default_factory=list)
    assistant_messages: List["AssistantMessageDTO"] = Field(default_factory=list)
    researches: List["ResearchDTO"] = Field(default_factory=list)

    class Config:
        orm_mode = True


