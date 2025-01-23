from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk
from src.database.postgres.models.base import updated_at


class Research(ModelBase):
    __tablename__ = "researches"
    __table_args__ = (
        Index("idx_research_owner_id", "owner_id"),
        UniqueConstraint("research_uuid", name="uq_research_uuid"),
        Index("idx_research_start_date", "start_date"),
        Index("idx_research_end_date", "end_date"),
        Index("idx_research_created_at", "created_at"),
        Index("idx_research_updated_at", "updated_at"),
        Index("idx_research_assistant_id", "assistant_id"),
        Index("idx_research_telegram_client_id", "telegram_client_id"),
    )

    research_id: Mapped[intpk]
    research_uuid: Mapped[Optional[str]]
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("research_owners.owner_id"))
    name: Mapped[Optional[str]]
    title: Mapped[Optional[str]]
    theme: Mapped[Optional[str]]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    descriptions: Mapped[Optional[str]]
    additional_information: Mapped[Optional[str]]

    assistant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assistants.assistant_id"))
    telegram_client_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("telegram_clients.client_id"))

    owner: Mapped["ResearchOwner"] = relationship(back_populates="researches")

    users: Mapped[list["User"]] = relationship(back_populates="researches", secondary="user_research")

    assistant: Mapped["Assistant"] = relationship(back_populates="research")

    status: Mapped["ResearchStatus"] = relationship(back_populates="researches")

    telegram_client: Mapped["TelegramClient"] = relationship(back_populates="researches")

    user_messages: Mapped[list["UserMessage"]] = relationship(back_populates="research")

    assistant_messages: Mapped[list["AssistantMessage"]] = relationship(back_populates="research")
