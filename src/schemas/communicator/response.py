
from typing import List, Dict

from pydantic import BaseModel


class SingleResponse(BaseModel):
    user_message: str
    response: str


class ContextResponse(BaseModel):
    context: List[Dict]
    response: str
