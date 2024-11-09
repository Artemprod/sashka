from enum import Enum

from pydantic import BaseModel, Field


from src.web.models.client import ClientConfigDTO


class ServiceTypes(Enum):
    WEB = "web"
    telegram = "telegram"


class ServiceData(BaseModel):
    user_id: int


class ServiceClientSignupDTO(BaseModel):
    service_type: ServiceTypes = Field(default=ServiceTypes.telegram.value)
    client_config: ClientConfigDTO
    service_data: ServiceData

    class Config:
        from_attributes = True


ServiceClientSignupDTO.model_rebuild()
