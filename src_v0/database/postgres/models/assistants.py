from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src_v0.database.postgres.models.base import ModelBase, intpk, str_1024, created_at


class Assistant(ModelBase):
    __tablename__ = 'assistants'

    assistant_id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String)
    system_prompt: Mapped[str] = mapped_column(String)
    user_prompt: Mapped[str] = mapped_column(String)

    # Поля с опциональными значениями
    first_message_prompt: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    middle_part_prompt: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
    last_message_prompt: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)

    created_at: Mapped[created_at]

    research: Mapped["Research"] = relationship(
        back_populates="assistant"
    )

    messages: Mapped[list["AssistantMessage"]] = relationship(
        back_populates="assistant")
