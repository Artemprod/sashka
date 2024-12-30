from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class AssistantDTOPost(BaseModel):
    name: str
    system_prompt: str
    user_prompt: str

    first_message_prompt: Optional[str] = None
    middle_part_prompt: Optional[str] = None
    last_message_prompt: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    for_conversation: bool = Field(default=False)

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


class AssistantDTOGet(AssistantDTOPost):
    assistant_id: int
