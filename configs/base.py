

import sys
from pathlib import Path

from pydantic_settings import BaseSettings

sys.path.append(str(Path(__file__).parent.parent))

class BaseConfig(BaseSettings):
    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        nested_model_default_partial_update = True
