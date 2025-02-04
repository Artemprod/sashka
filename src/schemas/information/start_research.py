from pydantic import BaseModel
from typing import Set


class NameInfo(BaseModel):
    names: Set[str]
    total: int


class UserInfo(BaseModel):
    correct_names: NameInfo
    wrong_names: NameInfo


UserInfo.model_rebuild()
