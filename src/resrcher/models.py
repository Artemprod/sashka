from datetime import datetime
from typing import Optional

from openai import BaseModel

from src.database.postgres.models.enum_types import ResearchStatusEnum


class ResearchCashDTO(BaseModel):
    research_id: Optional[int] = None
    research_status: Optional[ResearchStatusEnum] = None
    user_in_progress: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

