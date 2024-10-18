from datetime import datetime
from typing import Optional

from sqlalchemy import  Text,  Integer


from sqlalchemy.orm import Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk,  created_at


class PingPrompt(ModelBase):
    __tablename__ = 'ping_prompt'

    prompt_id: Mapped[intpk]
    ping_order_number: Mapped[int] = mapped_column(Integer)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[created_at]

