from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PingPromptDTO(BaseModel):
    prompt_id: int
    ping_order_number: int
    system_prompt: Optional[str]
    prompt: str
    created_at: Optional[datetime]
