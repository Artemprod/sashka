from typing import Optional
from pydantic import BaseModel


class ResearchOwnerDTO(BaseModel):

    name: str
    service_owner_id: int # Id в телеграме или другом мервисе
    second_name: Optional[str] = None
    phone_number: Optional[str] = None
    tg_link: Optional[str] = None
    language_code: Optional[str] = None
    service_id: int

    class Config:
        from_attributes = True 


class ResearchOwnerFullDTO(ResearchOwnerDTO):
    owner_id: int

    class Config:
        from_attributes = True 


class ResearchOwnerRelDTO(ResearchOwnerFullDTO):
    researches: list["ResearchDTO"]
    service: Optional["ServicesDTO"]

    class Config:
        from_attributes = True 
