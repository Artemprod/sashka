
from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at


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
