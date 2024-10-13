import platform
import sys
from pathlib import Path

from pydantic import BaseModel, Field, __version__
from typing import Union, Optional, Dict

from pyrogram.enums import ParseMode



APP_VERSION = f"Pyrogram {__version__}"
DEVICE_MODEL = f"{platform.python_implementation()} {platform.python_version()}"
SYSTEM_VERSION = f"{platform.system()} {platform.release()}"

class ClientConfigDTO(BaseModel):
    name: str
    api_id: str
    api_hash: str
    app_version: str = Field(default_factory=lambda: APP_VERSION)
    device_model: str = Field(default_factory=lambda: DEVICE_MODEL)
    system_version: str = Field(default_factory=lambda: SYSTEM_VERSION)
    lang_code: str = "ru"
    test_mode: bool = False
    bot_token: Optional[str] = None
    session_string: Optional[str] = None
    phone_number: Optional[str] = None
    phone_code: Optional[str] = None
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
