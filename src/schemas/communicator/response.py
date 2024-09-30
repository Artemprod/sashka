
from typing import List, Dict

from pydantic import BaseModel


class SingleResponseDTO(BaseModel):
    user_message: str
    response: str


class ContextResponseDTO(BaseModel):
    context: List[Dict]
    response: str
