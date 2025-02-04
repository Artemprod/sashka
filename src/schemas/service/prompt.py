from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PingPromptDTO(BaseModel):
    prompt_id: int
    ping_order_number: int
    system_prompt: Optional[str]
    prompt: str
    created_at: Optional[datetime]
