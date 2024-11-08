import sys
from pydantic import Field, field_validator

from configs.base import BaseConfig
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

class AIAPIBaseConfig(BaseConfig):
    https: bool = Field(False, validation_alias='API_HTTPS')
    response_timeout: int = Field(120, validation_alias='AI_API_TIMEOUT')
    host: str = Field("localhost", validation_alias='AI_API_HOST')
    port: str = Field("9193", validation_alias='AI_API_PORT')

    @field_validator("https",
                     mode='before')
    def split_str(cls, field_data):
        if isinstance(field_data, str):
            return "true" == field_data.lower()
        return field_data

    @property
    def http_base_url(self):
        return f"http://{self.host}:{self.port}/"

    @property
    def https_base_url(self):
        return f"https://{self.host}:{self.port}/"


class OpenAiApiConfigs(AIAPIBaseConfig):

    endpoint_prefix: str = Field("openai/request/", validation_alias='OPEN_AI_API_PREFIX')
    single_response: str = Field("single", validation_alias='SINGLE_REQUEST_ENDPOINT')
    context_response: str = Field("context", validation_alias='CONTEXT_REQUEST_ENDPOINT')

    @property
    def single_response_url(self):
        if not self.https:
            return f"{self.http_base_url}{self.endpoint_prefix}{self.single_response}"
        return f"{self.https}{self.endpoint_prefix}{self.single_response}"

    @property
    def context_response_url(self):
        if not self.https:
            return f"{self.http_base_url}{self.endpoint_prefix}{self.context_response}"
        return f"{self.https_base_url}{self.endpoint_prefix}{self.context_response}"


ai_api_endpoint_base_settings = AIAPIBaseConfig()
open_ai_api_endpoint_settings = OpenAiApiConfigs()

