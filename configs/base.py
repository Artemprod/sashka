from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
load_dotenv()

class BaseConfig(BaseSettings):
    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        nested_model_default_partial_update = True