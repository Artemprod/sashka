from pydantic import Field

from configs.base import BaseConfig


class S3StorageConfig(BaseConfig):

    access_key: str = Field(validation_alias='S3_ACCESS_KEY')
    secret_key: str = Field(validation_alias='S3_SECRET_KEY')
    endpoint_url: str = Field(validation_alias='S3_ENDPOINT_URL')
    bucket_name: str = Field(validation_alias='S3_BUCKET_NAME')


s3_configs = S3StorageConfig()
