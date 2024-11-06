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
from src.schemas.service.user import UserDTOFull, UserDTO, UserDTOBase
from src.services.communicator.checker import Checker
from src.services.communicator.messager import MessageFirstSend, ResearchMessageAnswer, CommonMessageAnswer, \
    MessageGeneratorTimeDelay, PingMessage
from src.services.communicator.prompt_generator import PromptGenerator, ExtendedPingPromptGenerator
from src.services.communicator.request import SingleRequest, ContextRequest
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.repository.storage import RepoStorage

from abc import ABC
from typing import Union

from src.schemas.service.queue import NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem, TelegramTimeDelaHeadersDTO, \
    TelegramSimpleHeadersDTO
from src.services.publisher.publisher import NatsPublisher


class TelegramCommunicator:
    """Класс для управления общением с ИИ через Telegram."""

    def __init__(self,
                 repository: "RepoStorage",
                 info_collector: "TelegramUserInformationCollector",
                 publisher: "NatsPublisher",
                 single_request: "SingleRequest",
                 context_request: "ContextRequest",
                 prompt_generator: "ExtendedPingPromptGenerator",
                 destination_configs: Optional[Dict] = None):

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

        self.ping_message = PingMessage(
            publisher=publisher,
            repository=repository,
            prompt_generator=prompt_generator,
            context_request=context_request
        )

    # TODO Вынести конфиги и закгрузку конфигов в отдельный модуль
    @staticmethod
    def _load_destination_configs() -> dict:
        return {
            "reply": NatsDestinationDTO(subject="test.message.conversation.send", stream="CONVERSATION"),
            "firs_message": NatsDestinationDTO(subject="test_4.messages.send.first", stream="WORK_QUEUE_4"),
        }

    async def make_first_message_distribution(self, research_id: int, users: List[UserDTOBase]):
        try:
            await self._first_message_distributes.handle(users=users,
                                                         destination_configs=self._destination_configs['firs_message'],
                                                         research_id=research_id)
        except Exception as e:
            raise e

    #TODO Вынести ответчик в отдельные классы например ответ на текстовое сообщение ответ на аудио ответ на картинку
    #TODO Возмодно вынести проверку пользвателя в базе данных их класса принциа единой отвесвтенности
    #TODO тогда уберуться ненужные методы в реплаер тут будет апи только для взаимодействия с ИИ и ответ
    async def reply_message(self, message_object: "IncomeUserMessageDTOQueue"):
        """Обрабатывает и отвечает на входящее сообщение."""

        try:
            check = await self._checker.check_user(user_telegram_id=message_object.from_user)

            if not check.user_in_db:
                # Попытка создания нового пользователя
                new_user = await self._add_new_user(message_object)

                if not new_user:
                    logger.error(f"Failed to create new user for telegram_id: {message_object.from_user}")
                    # Здесь можно добавить логику уведомления пользователя об ошибке
                    return
                else:
                    check.user_in_db = True

            if check.user_in_db:
                if not check.is_has_info:
                    # Собираем информацию о пользователе
                    asyncio.create_task(self._collect_user_information(message_object))

                # Обрабатываем сообщение независимо от того, есть ли информация о пользователе или нет
                await self._handle_message(message_object, check.user_research_id)
            else:
                logger.warning(f"User not in database: {message_object.from_user}")
                # Здесь можно добавить логику уведомления пользователя о необходимости регистрации

        except Exception as e:
            logger.error(f"An error occurred while processing the message from {message_object.from_user}: {e}")
            # Здесь можно добавить логику уведомления пользователя об ошибке


    async def _collect_user_information(self, message_object: "IncomeUserMessageDTOQueue"):

        try:
            # Получаем информацию о Telegram-клиенте
            telegram_client: TelegramClientDTOGet = await self._repository.client_repo.get_client_by_telegram_id(
                telegram_id=message_object.client_telegram_id
            )

            # Собираем информацию о пользователе
            user_info: List[UserDTO] = await self._info_collector.collect_users_information(
                users=[UserDTOBase(username=message_object.username, tg_user_id=message_object.from_user)],
                client=telegram_client
            )

            # Обновляем информацию о пользователях в базе данных
            for user in user_info:
                user.is_info = True
                await self._repository.user_in_research_repo.short.update_user_info(telegram_id=message_object.from_user,values=user.dict())
                logger.info(f"User {user.tg_user_id} information updated in database")



        except Exception as e:
            logger.error(f"Failed to collect or update user information: {e}")
            raise  # Перебрасываем ошибку, чтобы внешний код также мог её обработать



    async def ping_user(self, user: UserDTOBase, message_number,research_id):
        try:
            await self.ping_message.handle(user=user,
                                           message_number=message_number,
                                           research_id=research_id,
                                           destination_configs=self._destination_configs['reply'])
        except Exception as e:
            raise e

    async def _handle_message(self, message_object: "IncomeUserMessageDTOQueue",
                              user_research_id: Optional[str]):

        handler = self._message_research_answer if user_research_id else self._message_common_answer
        try:
            await handler.handle(
                message=message_object,
                destination_configs=self._destination_configs['reply'],
                research_id=user_research_id
            )
        except Exception as e:
            raise e

    async def _add_new_user(self, message_object: "IncomeUserMessageDTOQueue") -> Optional[List["UserDTOFull"]]:

        telegram_client: TelegramClientDTOGet = await self._repository.client_repo.get_client_by_telegram_id(
            telegram_id=message_object.client_telegram_id
        )
        user_info: List[UserDTO] = await self._info_collector.collect_users_information(
            users=[UserDTOBase(name=message_object.user_name,
                               tg_user_id=message_object.from_user)],
            client=telegram_client)
        new_users: list = []
        for user in user_info:
            new_users.append(await self._repository.user_in_research_repo.short.add_user(values=user.dict()))
            logger.info("Add new user in database")
        return new_users


async def main():
    repository = RepoStorage(database_session_manager=DatabaseSessionManager(
        database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))


    publisher = NatsPublisher()
    info_collector = TelegramUserInformationCollector(publisher=publisher)
    single_request = SingleRequest()
    context_request = ContextRequest()
    prompt_generator = PromptGenerator(repository=repository)
    comunicator = TelegramCommunicator(repository=repository,
                                       info_collector=info_collector,
                                       publisher=publisher,
                                       prompt_generator=prompt_generator,
                                       single_request=single_request,
                                       context_request=context_request,
                                       )
    message_object = IncomeUserMessageDTOQueue(from_user=2200682155,
                                               chat=2200682155,
                                               user_name='test_ai',
                                               media=False,
                                               voice=False,
                                               text="Тестовое сообщение ответь как нибудь",
                                               client_telegram_id=2200145162, )

    await comunicator.reply_message(message_object=message_object)


if __name__ == '__main__':
    asyncio.run(main())
