from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10


class ResearchOwner(ModelBase):
    __tablename__ = 'research_owners'

    owner_id: Mapped[intpk]
    name: Mapped[str]
    second_name: Mapped[Optional[str]]
    phone_number: Mapped[Optional[str]]
    service_owner_id:Mapped[int]

    tg_link: Mapped[Optional[str]]
    last_online_date: Mapped[Optional[datetime]]
    language_code: Mapped[Optional[str]]
    created_at: Mapped[created_at]

    service_id: Mapped[int] = mapped_column(ForeignKey("services.service_id"))

    service:Mapped["Services"] = relationship(
        back_populates="owners"
    )

    researches: Mapped[list["Research"]] = relationship(
        back_populates="owner"
    )

