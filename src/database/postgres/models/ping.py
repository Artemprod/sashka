from typing import Optional

from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk


class PingPrompt(ModelBase):
    __tablename__ = 'ping_prompt'

    prompt_id: Mapped[intpk]
    ping_order_number: Mapped[int] = mapped_column(Integer)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[created_at]

