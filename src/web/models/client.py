import sys
from pathlib import Path

from pydantic import BaseModel, Field, __version__
from typing import Union, Optional, Dict

from pyrogram.enums import ParseMode


class ClientConfigDTO(BaseModel):
    name: str
    api_id: str
    api_hash: str
    app_version: Optional[str]
    device_model: Optional[str]
    system_version: Optional[str]
    lang_code: str = "ru"
    test_mode: bool = False
    phone_number: Optional[str] = None
    password: Optional[str] = None
    workdir: str = Field(default_factory=lambda: str(Path(sys.argv[0]).parent))
    parse_mode: ParseMode = None

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

    @classmethod
    def from_orm(cls, orm_model):
        return cls(**orm_model.__dict__)

    def to_dict(self):
        return self.dict()

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)