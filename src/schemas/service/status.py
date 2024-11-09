from datetime import datetime
from datetime import timezone
from typing import List

from pydantic import BaseModel
from pydantic import Field

from src.database.postgres.models.enum_types import ResearchStatusEnum


class UserStatusDTO(BaseModel):
    user_id: int
    status_name: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

    class Config:
        from_attributes = True


class UserStatusDTOFull(UserStatusDTO):
    users: List["UserDTOFull"] = Field(default_factory=list)




class ResearchStatusDTO(BaseModel):
    research_id: int
    status_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResearchStatusDTOFull(ResearchStatusDTO):
    researches: List["ResearchDTOFull"] = Field(default_factory=list)
    class Config:
        from_attributes = True



class ResearchStatusName(BaseModel):
    status_name: ResearchStatusEnum
    class Config:
        from_attributes = True

