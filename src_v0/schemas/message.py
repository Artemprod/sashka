from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserMessageDTO(BaseModel):
    user_message_id: int
    from_user: int
    chat: int
    forwarded_from: Optional[str]
    reply_to_message_id: Optional[int]
    media: bool
    edit_date: Optional[datetime]
    voice: bool
    text: str
    created_at: datetime



class VoiceMessageDTO(BaseModel):
    voice_message_id: int
    file_id: str
    file_unique_id: str
    duration: Optional[int]
    mime_type: Optional[str]
    file_size: Optional[float]
    created_at: datetime
    user_message_id: int



class AssistantMessageDTO(BaseModel):
    assistant_message_id: int
    text: str
    chat_id: int
    to_user_id: int
    created_at: datetime
    assistant_id: int
    telegram_client_id: int


