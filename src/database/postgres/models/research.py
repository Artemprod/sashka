from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10, updated_at


class Research(ModelBase):
    __tablename__ = 'researches'
    research_id: Mapped[intpk]
    owner: Mapped[str]
    name: Mapped[str]
    title: Mapped[str]
    theme: Mapped[str]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    descriptions: Mapped[Optional[str]]
    additional_information: Mapped[Optional[str]]

    research_status_id: Mapped[int] = mapped_column(ForeignKey('research_status_name.status_id'))
    assistant_id: Mapped[int] = mapped_column(ForeignKey('assistants.assistant_id'))
    telegram_client_id: Mapped[int] = mapped_column(ForeignKey('telegram_clients.telegram_client_id'))

    users: Mapped[list["User"]] = relationship(
        back_populates="researches",
        secondary="user_research"
    )

    assistant: Mapped["Assistant"] = relationship(
        back_populates="research"
    )

    status: Mapped["ResearchStatusName"] = relationship(
        back_populates="researches")

    telegram_client: Mapped["TelegramClient"] = relationship(
        back_populates="researches"
    )
