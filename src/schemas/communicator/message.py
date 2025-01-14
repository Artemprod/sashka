from typing import Optional

from pydantic import BaseModel
from pydantic import field_validator


class IncomeUserMessageDTOQueue(BaseModel):

    message:str
    from_user: int
    first_name:str
    username: str
    chat: int
    media: bool
    voice: bool
    client_telegram_id: int
    s3_object_key: Optional[str] = None

    # Валидатор для поля media
    @field_validator('media', mode='before')
    def validate_media(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)

    # Валидатор для поля voice
    @field_validator('voice', mode='before')
    def validate_voice(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)
