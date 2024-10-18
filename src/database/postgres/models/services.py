from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.database.postgres.models.base import ModelBase, intpk, str_1024, created_at, str_2048, str_10, updated_at


class Services(ModelBase):
    __tablename__ = 'services'
    service_id: Mapped[intpk]
    name: Mapped[str]

    owners: Mapped[list["ResearchOwner"]] = relationship(
        back_populates="service"
    )
