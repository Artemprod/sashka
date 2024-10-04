


from typing import List, Dict

from pydantic import BaseModel


class PromptDTO(BaseModel):
    user_prompt: str
    system_prompt:str

