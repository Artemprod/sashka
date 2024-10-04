from typing import List, Dict, Optional

from pydantic import BaseModel


class NatsDestinationDTO(BaseModel):
    subject: str
    stream: Optional[str]
