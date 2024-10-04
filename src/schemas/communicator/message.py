from typing import List, Dict

from pydantic import BaseModel


class IncomeUserMessageDTOQueue(BaseModel):
    from_user: int
    chat: int
    media: bool
    voice: bool
    text: str
    client_telegram_id: int
