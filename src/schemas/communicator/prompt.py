


from typing import List, Dict, Optional

from pydantic import BaseModel


class PromptDTO(BaseModel):
    assistant_message: Optional[str] = None
    user_prompt: str
    system_prompt:str

