import sys
from datetime import timedelta
from pathlib import Path

from pydantic import Field, field_validator

from configs.base import BaseConfig

sys.path.append(str(Path(__file__).parent.parent))


class CommunicatorBaseConfigs(BaseConfig):
    ...


class FirstMessagePolicy(CommunicatorBaseConfigs):
    people_in_bunch: int = Field(10, validation_alias='COMMUNICATOR_PEOPLE_IN_BUNCH')
    delay_between_bunch: timedelta = Field(default=timedelta(hours=24),
                                           validation_alias='COMMUNICATOR_DELAY_BETWEEN_BUNCH_HOURS')
    delay_between_messages: timedelta = Field(default=timedelta(minutes=5),
                                              validation_alias='COMMUNICATOR_DELAY_BETWEEN_MESSAGE_IN_BUNCH_MINUTES')

    @field_validator('delay_between_bunch', mode='before')
    def validate_delay_between_bunch(cls, value):
        if isinstance(value, str) or isinstance(value, int):
            return timedelta(hours=int(value))
        raise ValueError('delay_between_bunch must be an int or string representing hours')

    @field_validator('delay_between_messages', mode='before')
    def validate_delay_between_messages(cls, value):
        if isinstance(value, str) or isinstance(value, int):
            return timedelta(minutes=int(value))
        raise ValueError('delay_between_messages must be an int or string representing minutes')


communicator_first_message_policy = FirstMessagePolicy()


