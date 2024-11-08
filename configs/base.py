from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        nested_model_default_partial_update = True