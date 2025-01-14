
from typing import Dict
from typing import List

from pydantic import BaseModel


class SingleResponseDTO(BaseModel):
    user_message: str
    response: str


class ContextResponseDTO(BaseModel):
    context: List[Dict]
    response: str


class TranscribeResponseDTO(BaseModel):
    text: str
