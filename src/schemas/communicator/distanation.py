from typing import Optional

from pydantic import BaseModel


class NatsDestinationDTO(BaseModel):
    subject: str
    stream: Optional[str]
