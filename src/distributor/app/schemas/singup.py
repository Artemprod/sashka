from pydantic import BaseModel

from src.distributor.telegram_client.pyro.client.model import ClientConfigDTO


class ServiceData(BaseModel):
    user_id: int


class TelegramServiceClientSignupDTO(BaseModel):
    service_type: str
    client_config: ClientConfigDTO
    service_data: ServiceData

    class Config:
        from_attributes = True
