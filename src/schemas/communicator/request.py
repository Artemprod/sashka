from typing import List, Dict, Optional

from pydantic import BaseModel


class SingleRequestDTO(BaseModel):
    assistant_message: Optional[str] = None
    user_prompt: str
    system_prompt: str


class ContextRequestDTO(BaseModel):
    context: List[Dict[str, str]]
    system_prompt: str
    user_prompt: str
