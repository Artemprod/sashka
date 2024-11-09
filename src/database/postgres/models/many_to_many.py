
from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, created_at


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
