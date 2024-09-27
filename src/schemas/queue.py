import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field

from src.schemas.client import TelegramClientDTO
from src.schemas.owner import ResearchOwnerDTO
from src.schemas.status import ResearchStatusDTO, ResearchStatusName
from src.schemas.user import UserDTO
from src_v0.schemas.assistant import AssistantDTO


# Base headers class
class NatsHeaders(BaseModel):
    ...


# Telegram specific headers inheriting from base headers
class NatsTelegramHeaders(NatsHeaders):
    telegram_client_name: Optional[str] = None
    tg_user_id: Optional[str] = None
    description: Optional[str] = None
    send_time: Optional[datetime] = Field(default_factory=lambda: datetime.now())


# Queue message DTO for stream
class NatsQueueMessageDTOStreem(BaseModel):
    message: str
    subject: str
    stream: str
    headers: Optional[NatsHeaders] = None

    class Config:
        arbitrary_types_allowed = True


# Queue message DTO for subject only
class NatsQueueMessageDTOSubject(BaseModel):
    message: str
    subject: str
    headers: Optional[NatsHeaders] = None

    class Config:
        arbitrary_types_allowed = True


# Rebuild the models if necessary
NatsHeaders.model_rebuild()
NatsQueueMessageDTOStreem.model_rebuild()
NatsQueueMessageDTOSubject.model_rebuild()
