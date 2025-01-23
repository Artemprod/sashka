import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from loguru import logger
from types_aiobotocore_s3.client import S3Client as S3ClientType


class S3Client:
    """
    S3 client
    """

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,  # access key from s3 storage [Required]
            "aws_secret_access_key": secret_key,  # secret key from s3 storage [Required]
            "endpoint_url": endpoint_url,  # endpoint for your s3 storage for selectel [https://s3.storage.selcloud.ru]
            "region_name": "ru-1",  # region name default [ru-1] [Optional]
            "config": AioConfig(s3={"addressing_style": "virtual"}),  # [Optional]
        }
        self.bucket_name = bucket_name  # bucket name [Get from storage]
        self.session = get_session()  # current session [async contextmanager]

    @asynccontextmanager
    async def get_client(self) -> S3ClientType:
        """
        This is an asynchronous context manager that creates and yields an S3 client.
        The client is created using the current session and the configuration parameters
        defined during the initialization of the S3Client class.

        The client is automatically closed when exiting the 'with' block.

        :return: An instance of S3ClientType which represents the S3 client.
        """
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(self, file_path: str):
        """
        This method uploads a file to the S3 bucket.
        :param file_path: The path to the file to be uploaded.
        :return: str file name in bucket
        """
        # Формируем уникальный id для названия файла и добавляем формат файла
        object_name = f"{uuid.uuid5(uuid.NAMESPACE_DNS, Path(file_path).name)}.{Path(file_path).name.split('.')[-1]}"
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

    async def delete_file(self, object_name: str):
        """
        This method deletes a file from the S3 bucket.
        :param object_name: name of the object to be deleted from the bucket.
        :return: None
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                await client.delete_object(Bucket=self.bucket_name, Key=object_name)
                logger.info(f"File {object_name} deleted from {self.bucket_name}")
        except ClientError as e:
            logger.info(f"Error deleting file: {e}")

    async def download_file(self, object_name: str, destination_path: str):
        """
        This method downloads a file from the S3 bucket to the specified destination path.
        :param object_name: object name to be downloaded from the bucket.
        :param destination_path: path where the file will be downloaded.
        :return: None
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                response = await client.get_object(Bucket=self.bucket_name, Key=object_name)
                data = await response["Body"].read()
                async with aiofiles.open(destination_path, "wb") as file:
                    await file.write(data)
                logger.info(f"File {object_name} downloaded to {destination_path}")
        except ClientError as e:
            logger.info(f"Error downloading file: {e}")

    async def get_all_object(self) -> list[str]:
        """
        This method lists all objects in the S3 bucket. For each object, it returns the key.
        :return: List of object keys in the bucket.
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                response = await client.list_objects_v2(Bucket=self.bucket_name)
                if "Contents" in response:
                    return [obj["Key"] for obj in response["Contents"]]
                return []
        except ClientError as e:
            logger.info(f"Error listing objects: {e}")
            return []

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

    async def generate_presigned_url(self, key: str, ExpiresIn: int = 1488) -> str:
        """
        This method generates a presigned URL for the object with the given key.
        :param ExpiresIn: the time of link will be available (sec)
        :param key: Object name for which the presigned URL is to be generated.
        :return: str: Presigned URL for the object. [Expires in 1488 seconds default]
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                response = await client.generate_presigned_url(
                    "get_object", Params={"Bucket": self.bucket_name, "Key": key}, ExpiresIn=ExpiresIn
                )
                return response
        except Exception as err:
            print(err)

    async def get_object_data(self, key) -> dict:
        """
        Get information of object, like when was created and how size of the object
        :param key: Object Name
        :return: dict
        """
        try:
            async with self.get_client() as client:
                client: S3ClientType
                response = await client.head_object(Bucket=self.bucket_name, Key=key)
                return response
        except Exception as err:
            print(err)
