from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from src_v0.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from src_v0.schemas.message import UserMessageDTO
from src_v0.schemas.research import UserResearchDTO
from src_v0.schemas.status import UserStatusDTO



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



    class Config:
        from_attributes = True 