import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from functools import cache
from random import randint
from typing import Union, List, Optional, Any, Tuple, Dict

from loguru import logger

from src.schemas.communicator.distanation import NatsDestinationDTO
from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.schemas.communicator.prompt import PromptDTO
from src.schemas.communicator.request import SingleRequestDTO, ContextRequestDTO
from src.schemas.communicator.response import SingleResponseDTO, ContextResponseDTO
from src.schemas.service.assistant import AssistantDTOGet
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.message import AssistantMessageDTOPost, UserMessageDTOPost
from src.schemas.service.user import UserDTOFull
from src.services.communicator.checker import Checker
from src.services.communicator.prompt_generator import PromptGenerator
from src.services.communicator.request import SingleRequest, ContextRequest
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.enum_types import UserStatusEnum
from src_v0.database.repository.storage import RepoStorage

from abc import ABC
from typing import Union

from src.schemas.service.queue import NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem, TelegramTimeDelaHeadersDTO, \
    TelegramSimpleHeadersDTO
from src.services.publisher.messager import NatsPublisher


class TelegramCommunicator:
    """
    Класс выполняет функцию общения
    отправляет запрос в ИИ получает и отправлет ответ клиенту

    """

    def __init__(self, repository: RepoStorage,
                 checker: "Checker"):
        self._repository = repository
        self.checker = checker

    async def make_first_message_distribution(self):
        ...

    async def reply_message(self, message_object):
        """
        Функция обабатывает входящее сообщение и решает в зависимости от того есть
        пользователь в базе или нет и типа входящего сообщения выбрать стратегию ответа
        :return:
        """

        # Провыерить пользователя
        # проверить тип сообщения
        # Ответить



async def main():
    storage = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
    c = Communicator(_repository=storage, )

    await c.send_first_message(resarch_id=41)


if __name__ == '__main__':
    asyncio.run(main())
