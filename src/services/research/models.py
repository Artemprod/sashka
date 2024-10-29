from pydantic import BaseModel


class PingDataQueueDTO(BaseModel):
    user: dict
    message_number: str
    research_id: str
