from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from sqlalchemy.orm import Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, created_at
from src.database.postgres.models.services import Services


class ResearchOwner(ModelBase):
    __tablename__ = 'research_owners'

    owner_id: Mapped[intpk]
    name: Mapped[str]
    second_name: Mapped[Optional[str]]
    phone_number: Mapped[Optional[str]]
    service_owner_id: Mapped[int] = mapped_column(BigInteger) # id пользователя в сервисе

    tg_link: Mapped[Optional[str]]
    last_online_date: Mapped[Optional[datetime]]
    language_code: Mapped[Optional[str]]
    created_at: Mapped[created_at]

    service_id: Mapped[int] = mapped_column(ForeignKey("services.service_id"))

    service: Mapped["Services"] = relationship(
        back_populates="owners"
    )

    researches: Mapped[list["Research"]] = relationship(
        back_populates="owner"
    )
