from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class ResearchDTO(BaseModel):
    
    research_uuid: Optional[str] = None
    name: Optional[str] = Field(default_factory=None)
    title: Optional[str] = Field(default_factory=None)
    theme: Optional[str] = Field(default_factory=None)
    start_date: datetime = datetime.now(timezone.utc)
    end_date: datetime
    descriptions: Optional[str] = Field(default_factory=None)
    additional_information: Optional[str] = Field(default_factory=None)
    assistant_id: int


class ResearchDTOFull(ResearchDTO):
    
    owner_id: int
    telegram_client_id: Optional[int]


class ResearchDTORel(ResearchDTOFull):

    owner: "ResearchOwnerDTO"
    telegram_client: "TelegramClientDTO"
    assistant: "AssistantDTO"
    status: "ResearchStatusDTO"
    users: List["UserDTO"] = Field(default_factory=list)
