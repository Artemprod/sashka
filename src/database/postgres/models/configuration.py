from sqlalchemy import Index
from sqlalchemy.orm import Mapped

from src.database.postgres.models.base import ModelBase
from src.database.postgres.models.base import created_at
from src.database.postgres.models.base import intpk


class Configuration(ModelBase):
    __tablename__ = "configuration"
    __table_args__ = (Index("idx_configuration_stop_word", "stop_word"),)

    configuration_id: Mapped[intpk]

    min_response_time: Mapped[int]
    max_response_time: Mapped[int]

    stop_word: Mapped[str]

    communicator_people_in_bunch: Mapped[int]
    communicator_delay_between_bunch_hours: Mapped[int]
    communicator_delay_between_message_in_bunch_minutes: Mapped[int]

    ping_max_messages: Mapped[int]
    ping_attempts_multiplier: Mapped[int]
    ping_interval: Mapped[int]

    ban_check_interval_in_minutes: Mapped[int]

    created_at: Mapped[created_at]
