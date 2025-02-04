from typing import List
from typing import Optional

from pydantic import BaseModel


class UserDTOBase(BaseModel):
    name: Optional[str]
    tg_user_id: Optional[int]


class CommandStartDiologDTO(BaseModel):
    research_id: int
    users: List[UserDTOBase]


class CommandPingUserDTO(BaseModel):
    research_id: int
    user: UserDTOBase
    message_number: int
