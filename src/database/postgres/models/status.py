from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10
from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum





class UserStatusName(ModelBase):
    __tablename__ = 'user_status_name'

    status_id: Mapped[intpk]
    status_name: Mapped[UserStatusEnum]

    users: Mapped[list["User"]] = relationship(
        back_populates="status",
    )


class ResearchStatusName(ModelBase):
    __tablename__ = 'research_status_name'

    status_id: Mapped[intpk]
    status_name: Mapped[ResearchStatusEnum]

    researches:Mapped[list["Research"]] = relationship(
        back_populates="status"
    )
