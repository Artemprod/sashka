from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy import Index
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk


class User(ModelBase):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_phone_number", "phone_number"),
        Index("idx_user_last_online_date", "last_online_date"),
        Index("idx_user_is_verified", "is_verified"),
        Index("idx_user_is_scam", "is_scam"),
        Index("idx_user_is_fake", "is_fake"),
        Index("idx_user_is_premium", "is_premium"),
        Index("idx_user_tg_link", "tg_link"),
        Index("idx_user_created_at", "created_at"),
    )

    user_id: Mapped[intpk]
    tg_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, unique=True)
    username: Mapped[Optional[str]] = mapped_column(nullable=True, unique=True)
    name: Mapped[Optional[str]] = mapped_column(nullable=True)
    second_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(nullable=True)
    tg_link: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_verified: Mapped[Optional[bool]] = mapped_column(nullable=True)
    is_scam: Mapped[Optional[bool]] = mapped_column(nullable=True)
    is_fake: Mapped[Optional[bool]] = mapped_column(nullable=True)
    is_premium: Mapped[Optional[bool]] = mapped_column(nullable=True)
    last_online_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_info: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[created_at]

    status: Mapped["UserStatus"] = relationship(
        back_populates="users",
    )

    messages: Mapped[list["UserMessage"]] = relationship(back_populates="user")

    assistant_messages: Mapped[list["AssistantMessage"]] = relationship(back_populates="to_user")

    researches: Mapped[list["Research"]] = relationship(back_populates="users", secondary="user_research")
