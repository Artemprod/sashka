from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime, Index, BigInteger
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src_v0.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10


class User(ModelBase):
    __tablename__ = 'users'
    user_id: Mapped[intpk]
    name: Mapped[str]
    second_name: Mapped[Optional[str]]
    phone_number: Mapped[Optional[str]]

    tg_user_id: Mapped[int] = mapped_column(BigInteger,nullable=False, unique=True)

    tg_link: Mapped[Optional[str]]
    is_verified: Mapped[Optional[bool]]
    is_scam: Mapped[Optional[bool]]
    is_fake: Mapped[Optional[bool]]
    is_premium: Mapped[Optional[bool]]
    last_online_date: Mapped[Optional[datetime]]
    language_code: Mapped[Optional[str]]
    created_at: Mapped[created_at]

    status: Mapped["UserStatus"] = relationship(
        back_populates="users",

    )

    messages: Mapped[list["UserMessage"]] = relationship(
        back_populates="user")

    assistant_messages: Mapped[list["AssistantMessage"]] = relationship(
        back_populates="to_user"
    )

    researches: Mapped[list["Research"]] = relationship(
        back_populates="users",
        secondary="user_research"
    )

    # __table_args__ = (
    #     Index("user_id_index", "tg_user_id","name" ,"" )
    # )
