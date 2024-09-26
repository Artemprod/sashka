from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src_v0.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10


class UserResearch(ModelBase):
    __tablename__ = 'user_research'

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.user_id',
                   ondelete="CASCADE"),
        primary_key=True
    )

    research_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('researches.research_id',
                   ondelete="CASCADE"),
        primary_key=True,

    )

    created_at: Mapped[created_at]
