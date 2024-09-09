from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10, updated_at
from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum


class UserStatus(ModelBase):
    __tablename__ = 'user_status'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True, nullable=False)
    status_name: Mapped[UserStatusEnum]
    users: Mapped[list["User"]] = relationship(
        back_populates="status",
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class ResearchStatus(ModelBase):
    __tablename__ = 'research_status'

    research_id: Mapped[int] = mapped_column(ForeignKey("researches.research_id"), primary_key=True, nullable=False)

    status_name: Mapped[ResearchStatusEnum]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    researches: Mapped[list["Research"]] = relationship(
        back_populates="status"
    )
