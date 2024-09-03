from src.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from src.schemas.message import AssistantMessageDTO


class AssistantDTO(BaseModel):
    assistant_id: int
    name: str
    system_prompt: str
    user_prompt: str
    created_at: datetime

    messages: list[AssistantMessageDTO]