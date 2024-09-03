from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from src.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from src.schemas.message import UserMessageDTO
from src.schemas.research import UserResearchDTO
from src.schemas.status import UserStatusDTO


class UserDTO(BaseModel):
    user_id: int
    name: str
    second_name: Optional[str]
    phone_number: Optional[str]
    tg_user_id: str
    tg_link: str
    is_verified: bool
    is_scam: bool
    is_fake: bool
    is_premium: bool
    last_online_date: Optional[datetime]
    language_code: str
    created_at: datetime

    statuses: list[UserStatusDTO]
    # researches: Optional[List[UserResearchDTO]]
    # messages: Optional[List[UserMessageDTO]]
