from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import updated_at
from src.database.postgres.models.enum_types import ResearchStatusEnum
from src.database.postgres.models.enum_types import UserStatusEnum


class UserStatus(ModelBase):
    __tablename__ = "user_status"
    __table_args__ = (
        Index("idx_user_status_status_name", "status_name"),
        Index("idx_user_status_created_at", "created_at"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), primary_key=True, nullable=False)
    status_name: Mapped[UserStatusEnum]
    users: Mapped[list["User"]] = relationship(
        back_populates="status",
    )

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class ResearchStatus(ModelBase):
    __tablename__ = "research_status"
    __table_args__ = (
        Index("idx_research_status_status_name", "status_name"),
        Index("idx_research_status_created_at", "created_at"),
    )

    research_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("researches.research_id"), primary_key=True, nullable=False
    )

    status_name: Mapped[ResearchStatusEnum]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    researches: Mapped[list["Research"]] = relationship(back_populates="status")
