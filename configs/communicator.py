import sys
from datetime import timedelta
from pathlib import Path

from pydantic import Field

from configs.base import BaseConfig

sys.path.append(str(Path(__file__).parent.parent))

class CommunicatorBaseConfigs(BaseConfig):
    ...


class FirstMessagePolicy(CommunicatorBaseConfigs):

    people_in_bunch: int = Field(10, validation_alias='COMMUNICATOR_PEOPLE_IN_BUNCH')
    delay_between_bunch: timedelta  = Field(default=timedelta(hours=24), validation_alias='COMMUNICATOR_DELAY_BETWEEN_BUNCH_HOURS')
    delay_between_messages: timedelta  = Field(default=timedelta(minutes=5), validation_alias='COMMUNICATOR_DELAY_BETWEEN_MESSAGE_IN_BUNCH_MINUTES')


communicator_first_message_policy = FirstMessagePolicy()


