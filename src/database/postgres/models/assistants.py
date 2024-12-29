from typing import Optional

from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk


class Assistant(ModelBase):
    __tablename__ = "assistants"

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

    research: Mapped["Research"] = relationship(back_populates="assistant")

    messages: Mapped[list["AssistantMessage"]] = relationship(back_populates="assistant")

    user_messages: Mapped[list["UserMessage"]] = relationship(back_populates="assistant")
