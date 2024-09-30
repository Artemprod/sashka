from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

from src_v0.database.postgres.models.enum_types import ResearchStatusEnum


class UserStatusDTO(BaseModel):
    user_id: int
    status_name: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class UserStatusDTOFull(UserStatusDTO):
    users: List["UserDTOFull"] = Field(default_factory=list)


class ResearchStatusDTO(BaseModel):
    research_id: int
    status_name: str
    created_at: datetime
    updated_at: datetime


class ResearchStatusDTOFull(ResearchStatusDTO):
    researches: List["ResearchDTOFull"] = Field(default_factory=list)


class ResearchStatusName(BaseModel):
    status_name: ResearchStatusEnum
