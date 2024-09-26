from typing import Optional
from pydantic import BaseModel


class ResearchOwnerDTO(BaseModel):
    name: str
    service_owner_id: int
    second_name: Optional[str] = None
    phone_number: Optional[str] = None
    tg_link: Optional[str] = None
    language_code: Optional[str] = None

    class Config:
        orm_mode = True


class ResearchOwnerRelDTO(ResearchOwnerDTO):

    researches: list["ResearchDTO"]
    service: Optional["ServicesDTO"]

    class Config:
        orm_mode = True
