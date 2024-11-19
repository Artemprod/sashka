from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk
from src.database.postgres.models.base import updated_at


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

    user_messages: Mapped[list["UserMessage"]] = relationship(
        back_populates="research")

    assistant_messages:Mapped[list["AssistantMessage"]] = relationship(
        back_populates="research")


