

from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class CheckerDTO(BaseModel):
    user_telegram_id: int
    user_in_db: bool
    user_research_id: Optional[int] = Field(default=None)
    is_has_info: bool
