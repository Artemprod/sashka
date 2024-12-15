import asyncio
from typing import Dict
from typing import List
from typing import Optional

from loguru import logger

from configs.nats_queues import nats_distributor_settings
from src.database.repository.storage import RepoStorage
from src.schemas.communicator.distanation import NatsDestinationDTO
from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.user import UserDTO
from src.schemas.service.user import UserDTOBase
from src.schemas.service.user import UserDTOFull
from src.services.communicator.checker import Checker

from src.services.communicator.messager import MessageFirstSend, ScheduledFirstMessage
from src.services.communicator.messager import PingMessage
from src.services.communicator.messager import ResearchMessageAnswer
from src.services.communicator.prompt_generator import ExtendedPingPromptGenerator
from src.services.communicator.request import ContextRequest
from src.services.communicator.request import SingleRequest
from src.services.parser.user.gather_info import TelegramUserInformationCollector
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
                 stop_word_checker: "StopWordChecker",
                 destination_configs: Optional[Dict] = None,
                 ):

        self._repository = repository
        self._info_collector = info_collector
        self._destination_configs = destination_configs or self._load_destination_configs()
        self._checker = Checker(repository=repository)
        # Инициализация компонентов для обработки сообщений
        # self._first_message_distributes = MessageFirstSend(
        #     publisher=publisher,
        #     repository=repository,
        #     single_request=single_request,
        #     prompt_generator=prompt_generator
        # )

        self._first_message_distributes = ScheduledFirstMessage(
            publisher=publisher,
            repository=repository,
            single_request=single_request,
            prompt_generator=prompt_generator
        )
        self._message_research_answer = ResearchMessageAnswer(
            publisher=publisher,
            repository=repository,
            prompt_generator=prompt_generator,
            context_request=context_request,
            stop_word_checker=stop_word_checker
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
            "reply": NatsDestinationDTO(subject=nats_distributor_settings.message.send_message.subject,
                                        stream=nats_distributor_settings.message.send_message.stream),
            "firs_message": NatsDestinationDTO(subject=nats_distributor_settings.message.first_message_message.subject,
                                               stream=nats_distributor_settings.message.first_message_message.stream),
        }

    async def make_first_message_distribution(self, research_id: int, users: List[UserDTOBase]):
        try:
            await self._first_message_distributes.handle(users=users,
                                                         destination_configs=self._destination_configs['reply'],
                                                         research_id=research_id)
        except Exception as e:
            raise e

    #TODO Вынести ответчик в отдельные классы например ответ на текстовое сообщение ответ на аудио ответ на картинку
    #TODO Возмодно вынести проверку пользвателя в базе данных их класса принциа единой отвесвтенности
    #TODO тогда уберуться ненужные методы в реплаер тут будет апи только для взаимодействия с ИИ и ответ
    #FIXME Как то можно вынести проврку ? Это можно сделать декоратором над функцией
    async def reply_message(self, message_object: "IncomeUserMessageDTOQueue"):
        """Обрабатывает и отвечает на входящее сообщение."""
        try:
            check = await self._checker.check_user(
                user_telegram_id=message_object.from_user,
                client_telegram_id=message_object.client_telegram_id
            )
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
                if not check.user_research_id:
                    logger.warning(f"User {message_object.from_user} not in reseserch ")
                    return
                if not check.is_active_status:
                    logger.warning(f"User {message_object.from_user} not active")
                    return
                # Обрабатываем сообщение
                await self._handle_message(message_object, check.user_research_id)
                logger.info(f"User {message_object.from_user} in reseserch {check.user_research_id}")
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

    async def _handle_message(self,
                              message_object: "IncomeUserMessageDTOQueue",
                              user_research_id:int):

        try:

            await self._message_research_answer.handle(
                message_object=message_object,
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
            users=[UserDTOBase(username=message_object.username,
                               tg_user_id=message_object.from_user)],
            client=telegram_client)
        new_users: list = []
        for user in user_info:
            new_users.append(await self._repository.user_in_research_repo.short.add_user(values=user.dict()))
            logger.info("Add new user in database")
        return new_users


