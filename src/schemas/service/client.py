from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class TelegramClientDTOPost(BaseModel):
    
    telegram_client_id:int
    name: str
    api_id: str
    api_hash: str
    app_version: str
    device_model: str
    system_version: str

    lang_code: Optional[str] = None
    test_mode: bool = False
    session_string: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    parse_mode: Optional[str] = 'html'
    workdir: Optional[str] = None
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True 


class TelegramClientDTOGet(TelegramClientDTOPost):
    
    client_id: int

    class Config:
        from_attributes = True 


class TelegramClientRelDTO(TelegramClientDTOGet):
    # связи
    messages: List["AssistantMessageDTO"] = []
    researches: List["ResearchDTO"] = []

    class Config:
        from_attributes = True 
