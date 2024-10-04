from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from src_v0.database.postgres.models.base import ModelBase, intpk, str_1024, created_at


class Assistant(ModelBase):
    __tablename__ = 'assistants'

    assistant_id: Mapped[intpk]
    name: Mapped[str]
    system_prompt: Mapped[str]
    user_prompt: Mapped[str]
    first_message_prompt: Optional[Mapped[str]]
    middle_part_prompt: Optional[Mapped[str]]
    last_message_prompt: Optional[Mapped[str]]
    created_at: Mapped[created_at]

    research: Mapped["Research"] = relationship(
        back_populates="assistant"
    )

    messages: Mapped[list["AssistantMessage"]] = relationship(
        back_populates="assistant")
