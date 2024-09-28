import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field

from src.schemas.client import TelegramClientDTO
from src.schemas.owner import ResearchOwnerDTO
from src.schemas.status import ResearchStatusDTO, ResearchStatusName
from src.schemas.user import UserDTO
from src_v0.schemas.assistant import AssistantDTO


class ResearchDTOPost(BaseModel):
    research_uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    title: Optional[str] = None
    theme: Optional[str] = None
    start_date: datetime = Field(default_factory=lambda: datetime.now())
    end_date: datetime = Field(default_factory=lambda: datetime.now() + timedelta(days=10))
    descriptions: Optional[str] = None
    additional_information: Optional[str] = None
    assistant_id: Optional[int]
    examinees_ids: list[int]

    class Config:
        arbitrary_types_allowed = True


class ResearchDTOGet(BaseModel):

    research_uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    title: Optional[str] = None
    theme: Optional[str] = None
    start_date: datetime = Field(default_factory=lambda: datetime.now())
    end_date: datetime = Field(default_factory=lambda: datetime.now() + timedelta(days=10))
    descriptions: Optional[str] = None
    additional_information: Optional[str] = None
    assistant_id: Optional[int]

    class Config:
        arbitrary_types_allowed = True


class ResearchDTOBeDb(ResearchDTOGet):
    owner_id: int
    telegram_client_id: Optional[int]


class ResearchDTOFull(ResearchDTOBeDb):
    research_id: int


class ResearchDTORel(ResearchDTOFull):

    owner: "ResearchOwnerDTO"
    telegram_client: "TelegramClientDTO"
    assistant: "AssistantDTO"
    status: ResearchStatusName
    users: List["UserDTO"] = Field(default_factory=list)


ResearchOwnerDTO.model_rebuild()
AssistantDTO.model_rebuild()
TelegramClientDTO.model_rebuild()
ResearchStatusName.model_rebuild()
UserDTO.model_rebuild()
ResearchDTORel.model_rebuild()
