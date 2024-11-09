from typing import Optional

from sqlalchemy import String, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database.postgres.models.base import ModelBase, intpk, created_at


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

    for_conversation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)

    created_at: Mapped[created_at]

    research: Mapped["Research"] = relationship(
        back_populates="assistant"
    )

    messages: Mapped[list["AssistantMessage"]] = relationship(
        back_populates="assistant")
