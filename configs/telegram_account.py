import sys
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic import field_validator

from configs.base import BaseConfig

sys.path.append(str(Path(__file__).parent.parent))


class TelegramRestrictedAccounts(BaseConfig):
    not_allowed_users_id: Optional[list[int]] = Field(validation_alias='NOT_ALLOWED_USERS_ID')
    not_allowed_users_usernames: Optional[list[str]] = Field(validation_alias='NOT_ALLOWED_USERS_NAMES')
    not_allowed_services: Optional[list[str]] = Field(validation_alias='NOT_ALLOWED_SERVICES')

    @field_validator('not_allowed_users_id', 'not_allowed_users_usernames', 'not_allowed_services',
                     mode='before')
    def split_str(cls, field_data):
        if isinstance(field_data, str):
            return field_data.split(',')
        return field_data


telegram_account_allowance_policy = TelegramRestrictedAccounts()
