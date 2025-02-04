from datetime import datetime

from pydantic import BaseModel


class ConfigurationCreateSchema(BaseModel):
    ban_check_interval_in_minutes: int

    min_response_time: int
    max_response_time: int

    stop_word: str

    communicator_people_in_bunch: int
    communicator_delay_between_bunch_hours: int
    communicator_delay_between_message_in_bunch_minutes: int

    ping_max_messages: int
    ping_attempts_multiplier: int
    ping_interval: int

    class Config:
        from_attributes = True


class ConfigurationSchema(ConfigurationCreateSchema):
    configuration_id: int
    created_at: datetime
