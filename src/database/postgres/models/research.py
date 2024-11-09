from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from sqlalchemy.orm import Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, created_at, updated_at


class Research(ModelBase):
    __tablename__ = 'researches'
    research_id: Mapped[intpk]
    research_uuid:Mapped[Optional[str]]
    owner_id: Mapped[int] = mapped_column(BigInteger,ForeignKey("research_owners.owner_id"))
    name: Mapped[Optional[str]]
    title: Mapped[Optional[str]]
    theme: Mapped[Optional[str]]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    descriptions: Mapped[Optional[str]]
    additional_information: Mapped[Optional[str]]


    assistant_id: Mapped[int] = mapped_column(BigInteger,ForeignKey('assistants.assistant_id'))
    telegram_client_id: Mapped[int] = mapped_column(BigInteger,ForeignKey('telegram_clients.client_id'))

    owner:Mapped["ResearchOwner"] = relationship(
        back_populates="researches"
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="researches",
        secondary="user_research"
    )

    assistant: Mapped["Assistant"] = relationship(
        back_populates="research"
    )

    status: Mapped["ResearchStatus"] = relationship(
        back_populates="researches")

    telegram_client: Mapped["TelegramClient"] = relationship(
        back_populates="researches"
    )
