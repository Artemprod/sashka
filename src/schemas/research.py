from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ResearchPost(BaseModel):
    owner: str
    name: str
    title: str
    theme: str
    assistant_id:int
    start_date: datetime
    end_date: datetime
    description: Optional[str]
    additional_information: Optional[str] # название компании и тд тп
    users: list





class ResearchDTO(BaseModel):
    research_id: int
    owner: str
    name: str
    title: str
    theme: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_id: int
    additional_information: Optional[str]
    assistant_id: int


class UserResearchDTO(BaseModel):
    id: int
    created_at: datetime
    status_id: int
    user_id: int
    research_id: int
