import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field

from configs.base import BaseConfig

load_dotenv()
sys.path.append(str(Path(__file__).parent.parent))


class S3_storage(BaseConfig):
    access_key: str = Field(default="21f1be9b04ab4f69b9eff8c0f1647878", validation_alias="ACCESS_KEY")
    secret_key: str = Field(default="f481d9aa71e64ec4b1adc4c4cfadd077", validation_alias="SECRET_KEY")
    endpoint_url: str = Field(default="https://s3.storage.selcloud.ru", validation_alias="ENDPOINT_URL")


s3_selectel_settings = S3_storage()
