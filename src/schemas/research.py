from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ResearchDTO(BaseModel):

    research_uuid: Optional[str] = None
    owner_id: int
    name: Optional[str] = None
    title: Optional[str] = None
    theme: Optional[str] = None
    start_date: datetime
    end_date: datetime


    descriptions: Optional[str] = None
    additional_information: Optional[str] = None

    assistant_id: int
    telegram_client_id: int







# class ResearchDTO(BaseModel):
#     research_id: int
#     owner: str
#     name: str
#     title: str
#     theme: str
#     start_date: datetime
#     end_date: datetime
#     created_at: datetime
#     updated_id: int
#     additional_information: Optional[str]
#     assistant_id: int


class UserResearchDTO(BaseModel):
    id: int
    created_at: datetime
    status_id: int
    user_id: int
    research_id: int


class ResearchOwnerDTO(BaseModel):

    name: str
    second_name: Optional[str] = None
    phone_number: Optional[str] = None
    service_owner_id: int
    tg_link: Optional[str] = None
    language_code: Optional[str] = None


    class Config:
        orm_mode = True