import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from loguru import logger
from types_aiobotocore_s3.client import S3Client as S3ClientType

from configs.s3_storage import s3_configs, S3StorageConfig


class S3Manager:
    def __init__(
            self,
            config: S3StorageConfig
    ):
        self.config = {
            "aws_access_key_id": config.access_key,
            "aws_secret_access_key": config.secret_key,
            "endpoint_url": config.endpoint_url,
            "region_name": 'ru-1',
            "config": AioConfig(s3={'addressing_style': 'virtual'})
        }
        self.bucket_name = config.bucket_name
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self) -> S3ClientType:
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(self, file_path: str) -> str:
        object_name = f"{uuid.uuid5(uuid.NAMESPACE_DNS, Path(file_path).name)}.{Path(file_path).suffix.lstrip('.')}"
        try:
            async with self.get_client() as client:
                client: S3ClientType
                async with aiofiles.open(file_path, "rb") as file:
                    await client.put_object(
                        Bucket=self.bucket_name,
                        Key=object_name,
                        Body=await file.read(),
                    )
                logger.info(f"File {object_name} uploaded to {self.bucket_name}")
                return object_name
        except ClientError as e:
            logger.info(f"Error uploading file: {e}")

    async def delete_file(self, object_key: str):
        try:
            async with self.get_client() as client:
                client: S3ClientType
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
                logger.info(f"File {object_key} deleted from {self.bucket_name}")
        except ClientError as e:
            logger.info(f"Error deleting file: {e}")

    async def get_bucket_access_control_list(self):
        """
        This method gets the access control list (ACL) for the S3 bucket.
        Don't use this method in this project
        :return: s3 bucket ACL
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                response = await client.get_bucket_acl(Bucket=self.bucket_name)
                return response
        except ClientError as e:
            logger.info(f"Error getting bucket ACL: {e}")

    async def generate_presigned_url(self, object_key: str, expires_in: int = 1488) -> str:
        """
        This method generates a presigned URL for the object with the given key.
        :param expires_in: the time of link will be available (sec)
        :param object_key: Object name for which the presigned URL is to be generated.
        :return: str: Presigned URL for the object. [Expires in 1488 seconds default]
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                response = await client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': object_key},
                    ExpiresIn=expires_in
                )
                return response
        except Exception as err:
            logger.warning(err)

    async def get_object_data(self, object_key: str) -> dict:
        """
        Get information of object, like when was created and how size of the object
        :param object_key: Object Name
        :return: dict
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                response = await client.head_object(Bucket=self.bucket_name, Key=object_key)
                return response
        except Exception as err:
            logger.warning(err)

    async def get_file_url_and_data(self, s3_object_key: str) -> tuple[str, dict]:
        presigned_url = await self.generate_presigned_url(s3_object_key)
        s3_object_data = await self.get_object_data(s3_object_key)
        return presigned_url, s3_object_data


s3_manager = S3Manager(config=s3_configs)
