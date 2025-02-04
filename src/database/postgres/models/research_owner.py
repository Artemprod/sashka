from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk
from src.database.postgres.models.services import Services


class ResearchOwner(ModelBase):
    __tablename__ = "research_owners"
    __table_args__ = (
        Index("idx_research_owner_service_owner_id", "service_owner_id"),
        Index("idx_research_owner_phone_number", "phone_number"),
        Index("idx_research_owner_tg_link", "tg_link"),
        Index("idx_research_owner_created_at", "created_at"),
    )

    owner_id: Mapped[intpk]
    name: Mapped[str]
    second_name: Mapped[Optional[str]]
    phone_number: Mapped[Optional[str]]
    service_owner_id: Mapped[int] = mapped_column(BigInteger)  # id пользователя в сервисе

    tg_link: Mapped[Optional[str]]
    last_online_date: Mapped[Optional[datetime]]
    language_code: Mapped[Optional[str]]
    created_at: Mapped[created_at]

    service_id: Mapped[int] = mapped_column(ForeignKey("services.service_id"))

    service: Mapped["Services"] = relationship(back_populates="owners")

    researches: Mapped[list["Research"]] = relationship(back_populates="owner")
