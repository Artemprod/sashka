import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from functools import cache
from random import randint
from typing import Union, List, Optional, Any, Tuple, Dict

from loguru import logger

from src.schemas.communicator.checker import CheckerDTO
from src.schemas.communicator.distanation import NatsDestinationDTO
from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.schemas.communicator.prompt import PromptDTO
from src.schemas.communicator.request import SingleRequestDTO, ContextRequestDTO
from src.schemas.communicator.response import SingleResponseDTO, ContextResponseDTO
from src.schemas.service.assistant import AssistantDTOGet
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.message import AssistantMessageDTOPost, UserMessageDTOPost
from src.schemas.service.user import UserDTOFull, UserDTO
from src.services.communicator.checker import Checker
from src.services.communicator.messager import MessageFirstSend, ResearchMessageAnswer, CommonMessageAnswer, \
    MessageGeneratorTimeDelay
from src.services.communicator.prompt_generator import PromptGenerator
from src.services.communicator.request import SingleRequest, ContextRequest
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.enum_types import UserStatusEnum
from src_v0.database.repository.storage import RepoStorage

from abc import ABC
from typing import Union

from src.schemas.service.queue import NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem, TelegramTimeDelaHeadersDTO, \
    TelegramSimpleHeadersDTO
from src.services.publisher.messager import NatsPublisher


class TelegramCommunicator:
    """Класс для управления общением с ИИ через Telegram."""

    def __init__(self,
                 repository: "RepoStorage",
                 info_collector: "TelegramUserInformationCollector",
                 publisher: "NatsPublisher",
                 single_request: "SingleRequest",
                 context_request: "ContextRequest",
                 prompt_generator: "PromptGenerator",
                 destination_configs: Optional["NatsDestinationDTO"] = None):
        self._repository = repository
        self._info_collector = info_collector
        self._destination_configs = destination_configs or self._load_destination_configs()

        self._checker = Checker(repository=repository)
        # Инициализация компонентов для обработки сообщений
        self._first_message_distributes = MessageFirstSend(
            publisher=publisher,
            repository=repository,
            single_request=single_request,
            prompt_generator=prompt_generator
        )
        self._message_research_answer = ResearchMessageAnswer(
            publisher=publisher,
            repository=repository,
            prompt_generator=prompt_generator,
            context_request=context_request
        )
        self._message_common_answer = CommonMessageAnswer(
            publisher=publisher,
            repository=repository,
            prompt_generator=prompt_generator,
            context_request=context_request
        )

    @staticmethod
    def _load_destination_configs() -> "NatsDestinationDTO":
        subject, stream = ...  # Заполните эти параметры реальными значениями
        return NatsDestinationDTO(subject=subject, stream=stream)

    async def make_first_message_distribution(self):
        # Реализация метода
        pass

    async def reply_message(self, message_object: "IncomeUserMessageDTOQueue"):
        """Обрабатывает и отвечает на входящее сообщение."""
        check = await self._checker.check_user(user_telegram_id=message_object.from_user)

        if not check.user_in_db:
            new_user = await self._add_new_user(message_object)
            if new_user:
                check.user_in_db = True
            else:
                logger.error(f"Failed to create new user for telegram_id: {message_object.from_user}")
                return  # Можно отправить пользователю сообщение об ошибке

        if check.user_in_db:
            await self._handle_message(message_object, check.user_research_id)
        else:
            logger.warning(f"User not in database: {message_object.from_user}")
            # Можно отправить сообщение пользователю о необходимости регистрации

    async def _handle_message(self, message_object: "IncomeUserMessageDTOQueue", user_research_id: Optional[str]):

        handler = self._message_research_answer if user_research_id else self._message_common_answer
        try:
            await handler.handle(
                message=message_object,
                destination_configs=self._destination_configs,
                research_id=user_research_id
            )
        except Exception as e:
            # Здесь можно добавить дополнительную обработку ошибок (например, логирование)
            raise

    async def _add_new_user(self, message_object: "IncomeUserMessageDTOQueue") -> Optional["UserDTOFull"]:
        async with self._info_collector as collector:
            telegram_client = await self._repository.client_repo.get_client_by_telegram_id(
                telegram_id=message_object.client_telegram_id
            )
            user_info = await collector.collect_users_information(
                user_telegram_ids=[message_object.from_user],
                client_name=telegram_client
            )
            return await self._repository.user_in_research_repo.short.add_user(values=user_info.dict())


async def main():
    repository = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))

    info_collector = TelegramUserInformationCollector()
    publisher = NatsPublisher()
    single_request = SingleRequest()
    context_request = ContextRequest()
    prompt_generator = PromptGenerator(repository=repository)
    destination_configs = NatsDestinationDTO()
    comunicator = TelegramCommunicator(repository=repository,
                                       info_collector=info_collector,
                                       publisher=publisher,
                                       prompt_generator=prompt_generator,
                                       single_request=single_request,
                                       context_request=context_request,
                                       destination_configs=destination_configs
                                       )
    message_object = IncomeUserMessageDTOQueue()

    await comunicator.reply_message()


if __name__ == '__main__':
    asyncio.run(main())
