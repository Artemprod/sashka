from datetime import datetime
from typing import Set

from pydantic import BaseModel


class NameInfo(BaseModel):
    names: Set[str]
    total: int


class UserInfo(BaseModel):
    correct_names: NameInfo
    wrong_names: NameInfo


class ResponseScheme(BaseModel):
    research_id: int
    start_time: datetime
    users_info: UserInfo

UserInfo.model_rebuild()
