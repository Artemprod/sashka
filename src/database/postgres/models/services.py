
from sqlalchemy.orm import relationship

from sqlalchemy.orm import Mapped
from src.database.postgres.models.base import ModelBase, intpk


class Services(ModelBase):
    __tablename__ = 'services'
    service_id: Mapped[intpk]
    name: Mapped[str]

    owners: Mapped[list["ResearchOwner"]] = relationship(
        back_populates="service"
    )
