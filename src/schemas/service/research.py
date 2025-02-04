import uuid
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from typing import List, Union
from typing import Optional

import pytz
from pydantic import BaseModel, field_validator
from pydantic import Field

from src.schemas.service.assistant import AssistantDTOGet
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.status import ResearchStatusName
from src.schemas.service.user import UserDTO


class ResearchDTOPost(BaseModel):
    research_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), example="123e4567-e89b-12d3-a456-426614174000")
    telegram_client_id: int = Field(..., example=1234)
    name: Optional[str] = Field(None, example="Research Name")
    title: Optional[str] = Field(None, example="Research Title")
    theme: Optional[str] = Field(None, example="Research Theme")
    start_date: Union[datetime, str] = Field(default_factory=lambda: datetime.now().replace(tzinfo=None))
    end_date: datetime = Field(default_factory=lambda: (datetime.now() + timedelta(days=10)).replace(tzinfo=None))
    timezone_info: Optional[str] = Field(default_factory=lambda: datetime.now().astimezone().tzinfo, example="UTC")
    descriptions: Optional[str] = Field(None, example="Some descriptions")
    additional_information: Optional[str] = Field(None, example="Additional Information")
    assistant_id: Optional[int] = Field(None, example=1)
    examinees_user_names: List[str] = Field(default_factory=list, example=["user1", "user2"])

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


class ResearchDTOGet(BaseModel):
    research_uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    title: Optional[str] = None
    theme: Optional[str] = None
    start_date: datetime
    end_date: datetime
    descriptions: Optional[str] = None
    additional_information: Optional[str] = None
    assistant_id: Optional[int]

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


class ResearchDTOBeDb(ResearchDTOGet):
    owner_id: int
    telegram_client_id: Optional[int]


class ResearchDTOFull(ResearchDTOBeDb):
    research_id: int


class ResearchDTORel(ResearchDTOFull):
    owner: "ResearchOwnerDTO"
    telegram_client: "TelegramClientDTOGet"
    assistant: AssistantDTOGet
    status: ResearchStatusName
    users: List[UserDTO] = Field(default_factory=list)

    class Config:
        from_attributes = True
