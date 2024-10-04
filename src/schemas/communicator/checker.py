

from typing import List, Dict, Optional, Union

from pydantic import BaseModel, Field


class CheckerDTO(BaseModel):
    user_telegram_id: int
    user_in_db: bool
    user_research_id: Optional[int] = Field(default=None)
