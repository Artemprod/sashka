from typing import List, Dict

from pydantic import BaseModel


class SingleRequestDTO(BaseModel):
    user_prompt: str
    system_prompt: str


class ContextRequestDTO(BaseModel):
    context: List[Dict[str, str]]
    system_prompt: str
