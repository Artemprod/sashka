from src_v0.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel



class UserStatusNameDTO(BaseModel):
    status_id: int
    status: UserStatusEnum

class UserStatusDTO(BaseModel):
    id: int
    created_at: datetime
    status_id: int
    user_id: int
    status: UserStatusNameDTO


class ResearchStatusNameDTO(BaseModel):
    status_id: int
    status: ResearchStatusEnum


class ResearchStatusDTO(BaseModel):
    id: int
    created_at: datetime
    status_id: int
    research_id: int
    status: ResearchStatusNameDTO