from datetime import datetime, timedelta
from pydantic import Field, field_validator
from configs.base import BaseConfig

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

class CommunicatorBaseConfigs(BaseConfig):
    ...


class FirstMessagePolicy(CommunicatorBaseConfigs):

    people_in_bunch: int = Field(10, validation_alias='COMMUNICATOR_PEOPLE_IN_BUNCH')
    delay_between_bunch: datetime = Field(default=timedelta(hours=24), validation_alias='COMMUNICATOR_DELAY_BETWEEN_BUNCH_HOURS')
    delay_between_messages: datetime = Field(default=timedelta(minutes=5), validation_alias='COMMUNICATOR_DELAY_BETWEEN_MESSAGE_IN_BUNCH_MINUTES')


communicator_first_message_policy = FirstMessagePolicy()


