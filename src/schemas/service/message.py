from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserMessageDTOPost(BaseModel):

    user_telegram_id: int
    chat_id: int
    research_id: int
    telegram_client_id: int
    assistant_id: int

    forwarded_from: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    media: bool
    edit_date: Optional[datetime] = None
    voice: bool
    text: str

    class Config:
        from_attributes = True


class UserMessageDTOGet(BaseModel):

    message_id: int

    user_telegram_id:int
    chat_id:int
    research_id:int
    telegram_client_id:int
    assistant_id:int

    forwarded_from: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    media: bool
    edit_date: Optional[datetime] = None
    voice: bool
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssistantMessageDTOPost(BaseModel):

    text: str

    user_telegram_id:int
    assistant_id:int
    chat_id:int
    telegram_client_id:int
    research_id:int


    class Config:
        from_attributes = True


class AssistantMessageDTOGet(BaseModel):

    message_id: int
    text: str

    user_telegram_id:int
    assistant_id:int
    chat_id:int
    telegram_client_id:int
    research_id:int

    created_at: datetime


    class Config:
        from_attributes = True


class VoiceMessageDTOPost(BaseModel):
    file_id: str
    file_unique_id: str
    duration: Optional[int] = None
    mime_type: Optional[str] = None
    file_size: Optional[float] = None

    class Config:
        from_attributes = True


class VoiceMessageDTOGet(BaseModel):
    voice_message_id: int
    file_id: str
    file_unique_id: str
    duration: Optional[int] = None
    mime_type: Optional[str] = None
    file_size: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
