import asyncio
from abc import ABC, abstractmethod
from typing import Union

import aiohttp
from aiohttp import ClientSession
from loguru import logger

from src.schemas.communicator.request import ContextRequestDTO, SingleRequestDTO
from src.schemas.communicator.response import ContextResponseDTO, SingleResponseDTO


class AiConnector(ABC):
    """
    Задача этого типа класса общаться по API-запросам с сервером, где находится ИИ.
    """

    def __init__(self, settings: dict = None):
        self.settings = settings or self._load_settings()

    @staticmethod
    def _load_settings():
        return {
            'api_url': "http://localhost:9193/openai/request/",
            'timeout': 120  # Default timeout in seconds
        }

    @abstractmethod
    async def get_response(self, *args, **kwargs):
        pass

    async def send_request(self, url: str, session: ClientSession, send_object):
        try:

            async with session.post(
                    url=self.settings['api_url'] + url,
                    json=send_object.dict(),
                    timeout=self.settings.get('timeout')
            ) as result:
                result.raise_for_status()  # Ensure the response status is OK
                response_data = await result.json()
                return response_data

        except aiohttp.ClientError as e:
            logger.error(f"Client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def perform_request(self, send_object, url):
        async with aiohttp.ClientSession() as session:
            return await self.send_request(url=url, session=session, send_object=send_object)


class ContextRequest(AiConnector):

    async def get_response(self, context_obj: 'ContextRequestDTO') -> 'ContextResponseDTO':
        # Использование базового метода для управления сессией и обработкой исключений
        response = await self.perform_request(send_object=context_obj,url="context")
        return ContextResponseDTO(**response)


class SingleRequest(AiConnector):

    async def get_response(self, single_obj: 'SingleRequestDTO') -> 'SingleResponseDTO':
        # Использование базового метода для управления сессией и обработкой исключений
        response = await self.perform_request(send_object=single_obj, url="single")
        return SingleResponseDTO(**response)


