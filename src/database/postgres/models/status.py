from sqlalchemy import ForeignKey, BigInteger

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, created_at, updated_at
from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum


class UserStatus(ModelBase):
    __tablename__ = 'user_status'

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), primary_key=True, nullable=False)
    status_name: Mapped[UserStatusEnum]
    users: Mapped[list["User"]] = relationship(
        back_populates="status",
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class ResearchStatus(ModelBase):
    __tablename__ = 'research_status'

    research_id: Mapped[int] = mapped_column(BigInteger,ForeignKey("researches.research_id"), primary_key=True, nullable=False)

    status_name: Mapped[ResearchStatusEnum]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    researches: Mapped[list["Research"]] = relationship(
        back_populates="status"
    )
