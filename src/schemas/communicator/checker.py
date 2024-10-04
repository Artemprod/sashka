

from typing import List, Dict, Optional, Union

from pydantic import BaseModel, Field


class CheckerDTO(BaseModel):
    user_telegram_id: int
    user_in_db: bool
    user_research_id: Optional[Union[int, List]] = Field(default=None)
