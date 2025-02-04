from sqlalchemy import Index
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import intpk


class Services(ModelBase):
    __tablename__ = "services"
    __table_args__ = (Index("idx_service_name", "name"),)

    service_id: Mapped[intpk]
    name: Mapped[str]

    owners: Mapped[list["ResearchOwner"]] = relationship(back_populates="service")
