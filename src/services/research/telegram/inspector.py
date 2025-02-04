import asyncio
import json
import math
import re
from asyncio import Task
from datetime import datetime
from datetime import timedelta
from typing import Dict
from typing import List
from typing import Optional
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from mako.testing.helpers import result_lines

from configs.database import database_postgres_settings
from configs.nats_queues import nats_subscriber_communicator_settings
from configs.research import research_pingator_settings
from re import Pattern

from src.database.postgres.models.enum_types import ResearchStatusEnum
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.repository.storage import RepoStorage
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.schemas.service.research import ResearchDTOFull
from src.schemas.service.user import UserDTOBase
from src.schemas.service.user import UserDTOFull
from src.schemas.service.user import UserDTQueue
from src.services.exceptions.research import (
    UntimelyCompletionError,
    ResearchCompletionError,
    UserAndResearchInProgressError,
    UserInProgressError,
    ResearchStatusInProgressError,
)
from src.services.publisher.publisher import NatsPublisher
from src.services.research.models import PingDataQueueDTO
from src.services.research.telegram.decorators.finish_reserch import move_users_to_archive
from src.services.research.utils import CyclePingAttemptCalculator
from src.services.scheduler.manager import AsyncRedisApschedulerManager

from src.web.models.configuration import ConfigurationSchema
from src.utils.wrappers import async_wrap


# TODO Вынести во всех классах reserch id в инициализхатор классса потому что классы являются частю фасада
class BaseStopper:
    def __init__(self, repository, stopper):
        self.repository = repository
        self.stopper = stopper
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, int]:
        return {"delay_check_interval": 2}


class ResearchStarter:
    def __init__(self, repository: RepoStorage, publisher: NatsPublisher):
        self.repository = repository
        self.publisher = publisher
        self.settings = self._load_seatings()

    def _load_seatings(self):
        return {
            "command_subject": nats_subscriber_communicator_settings.commands.start_dialog,
            "answer_to_message": nats_subscriber_communicator_settings.commands.answer_to_message
        }

    async def start_up_research(self, research_id: int) -> None:
        """Начинает исследование, разослав сообщения пользователям."""

        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id, status=ResearchStatusEnum.IN_PROGRESS
        )
        user_group: List[UserDTOFull] = await self._get_users_in_research(research_id)

        users_dto = self._convert_users_to_dto(user_group)
        await self._publish_start_dialog_command(users=users_dto, research_id=research_id)

        logger.info("Команда на запуск исследования отправлена ")

    async def _publish_start_dialog_command(self, users: List[dict], research_id: int):
        subject_message: NatsQueueMessageDTOSubject = NatsQueueMessageDTOSubject(
            message="",
            subject=self.settings["command_subject"],
            headers={"users": json.dumps(users), "research_id": str(research_id)},
        )
        try:
            await self.publisher.publish_message_to_subject(subject_message=subject_message)

        except Exception as e:
            raise e

    async def _get_users_in_research(self, research_id) -> List[UserDTOFull]:
        users_in_research: List[
            UserDTOFull
        ] = await self.repository.user_in_research_repo.short.get_users_by_research_id(research_id=research_id)
        return users_in_research

    @staticmethod
    def _convert_users_to_dto(users: List[UserDTOFull]) -> List[dict]:
        """
        Преобразует список объектов UserDTOFull в формат DTO.
        """
        return [
            UserDTOBase(
                username=user.username,
                tg_user_id=user.tg_user_id
            ).model_dump() for user in users
        ]


class ResearchStopper:
    def __init__(self, repository, notifier=None):
        """
        Инициализация класса для остановки исследования.

        :param repository: Репозиторий для работы с данными.
        :param notifier: Необязательный нотификатор.
        """
        self.repository = repository
        self.notifier = notifier

    async def complete_research(self, research_id: int) -> int:
        """
        Завершает исследование, меняя статусы пользователей и исследования.

        :param research_id: Идентификатор исследования.
        :raises: Exception при ошибке завершения исследования.
        """

        user_group = await self._get_users_in_research(research_id)
        logger.info("Получен список пользователей для завершения исследования")

        # изменение статусов
        await self._update_research_status(research_id)
        await self._update_user_statuses(user_group)

        # Проверка корректности завершения
        users_in_progress = await self._get_users_in_progress(research_id)
        research_status = await self._get_research_status(research_id)

        # Условия не корректного завершения исследования
        if users_in_progress and research_status != ResearchStatusEnum.DONE.value:
            logger.warning("Некорректное завершение. Пользователи и исследование в процессе")
            raise UserAndResearchInProgressError()
        elif users_in_progress:
            logger.warning("Некорректное завершение.Пользователи остаются в процессе")
            raise UserInProgressError()
        elif research_status != ResearchStatusEnum.DONE.value:
            logger.warning("Некорректное завершение. Статус исследования не сменён на DONE")
            raise ResearchStatusInProgressError()
        try:
            await self.repository.in_research_repo.transfer_service.transfer_users(research_id)
            logger.info(f"Исследование {research_id} завершено успешно")
            return 1
        except Exception as e:
            raise

    async def _update_research_status(self, research_id: int) -> None:
        """Обновление статуса исследования."""
        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id, status=ResearchStatusEnum.DONE
        )
        logger.info(f"Статус исследования {research_id} обновлён на DONE")

    async def _update_user_statuses(self, user_group: List[UserDTOFull]) -> None:
        """Обновление статусов пользователей."""
        user_ids = [user.user_id for user in user_group]
        await self.repository.status_repo.user_status.update_status_group_of_user(
            user_group=user_ids, status=UserStatusEnum.DONE
        )
        logger.info(f"Статусы пользователей в группе {user_group} обновлены на DONE")

    async def _get_users_in_research(self, research_id) -> List[UserDTOFull]:
        return await self.repository.user_in_research_repo.short.get_users_by_research_id(
            research_id=research_id
        )

    async def _get_users_in_progress(self, research_id) -> int:
        users_in_progress = await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )
        return len(users_in_progress)

    async def _get_research_status(self, research_id: int) -> ResearchStatusEnum:
        """Получение текущего статуса исследования."""
        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        return research_status.status_name


class ResearchBanner(ResearchStarter):

    async def ban_research(self, research_id: int):
        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id,
            status=ResearchStatusEnum.BANNED
        )
        logger.info(f"Статус исследования {research_id} обновлён на BANNED")

    async def unban_research(self, research_id: int):
        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id,
            status=ResearchStatusEnum.IN_PROGRESS
        )

        users_without_first_message: List[UserDTOFull] = \
            await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
                research_id=research_id,
                status=UserStatusEnum.WAIT
            )

        users_without_answered_message: List[UserDTOFull] = \
            await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
                research_id=research_id,
                status=UserStatusEnum.NOT_ANSWERED
            )

        await self._publish_start_dialog_command(
            users=self._convert_users_to_dto(users_without_first_message),
            research_id=research_id
        )

        await self._publish_answer_to_message(
            users=self._convert_users_to_dto(users_without_answered_message),
            research_id=research_id
        )

    async def _publish_answer_to_message(
            self,
            users: List[dict],
            research_id: int
    ):
        subject_message: NatsQueueMessageDTOSubject = NatsQueueMessageDTOSubject(
            message="",
            subject=self.settings["answer_to_message"],
            headers={
                "users": json.dumps(users),
                "research_id": str(research_id)
            },
        )
        await self.publisher.publish_message_to_subject(subject_message=subject_message)


class UserDoneStopper(BaseStopper):
    async def monitor_user_status(self, research_id: int) -> int:
        while True:
            # Проверка наличие активных пользователей
            users_in_progress = await self._get_users_in_progress(research_id)
            if not users_in_progress:
                logger.info(f"Завершаю исследование {research_id}, так как закончились пользователи")
                return 1

            await asyncio.sleep(self.settings["delay_check_interval"])

    async def _get_users_in_progress(self, research_id: int) -> int:
        # Получение пользователей с активным статусом
        users_in_progress = await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )
        users_in_wait = await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.WAIT
        )
        return len(users_in_progress) + len(users_in_wait)


class ResearchStatusStopper(BaseStopper):
    async def monitor_research_status(self, research_id: int) -> int:
        while True:
            research_status = await self._get_research_current_status(research_id)
            # Проверка на смену статуса исследования
            if research_status not in [ResearchStatusEnum.IN_PROGRESS.value, ResearchStatusEnum.WAIT.value]:
                logger.info(f"Завершаю исследование {research_id} по смене статуса. Статус {research_status}")
                return 1
            await asyncio.sleep(self.settings["delay_check_interval"])

    async def _get_research_current_status(self, research_id: int) -> str:
        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        return research_status.status_name


class ResearchOverChecker(BaseStopper):
    async def monitor_time_completion(self, research_id: int):
        """
        Универсальный метод для проверки завершения исследования (по времени
        или по статусу пользователей). Проверяет на двух уровнях: по энд-дате и
        по количеству пользователей в процессе.
        """
        end_date = await self._get_research_end_date(research_id)

        if not end_date:
            logger.warning(f"Исследование {research_id} не имеет конечной даты")
            return

        while True:
            current_time = datetime.now(pytz.utc).replace(tzinfo=None)

            # Проверка на конечную дату
            if current_time >= end_date:
                logger.info(
                    f"Завершаю исследование {research_id} по истечению времени, время завершения {current_time}"
                )
                return 1


            await asyncio.sleep(self.settings["delay_check_interval"])

    async def _get_research_end_date(self, research_id: int) -> Optional[datetime]:
        research = await self.repository.research_repo.short.get_research_by_id(research_id=research_id)

        # Быстрый возврат, если даты нет
        if not research.end_date:
            return None

        # Если время уже наивное, возвращаем как есть
        if research.end_date.tzinfo is None:
            return research.end_date

        # Конвертируем в UTC, если timezone отличается
        return research.end_date.astimezone(pytz.utc).replace(tzinfo=None)


class StopWordChecker:
    """
    Класс для поиска стоп-слова в сообщениях и завершения диалога при его нахождении.
    """

    def __init__(self, repo: "RepoStorage"):
        """
        :param repo: Репозиторий для работы с данными.
        """
        self.repo = repo

    async def _get_stop_phrase(self) -> str:
        configuraion = await self.repo.configuration_repo.get()
        logger.debug(f"________________CONFIG_stop {configuraion}")
        return configuraion.stop_word

    async def _get_stop_pattern(self) -> Pattern:
        stop_phrase = await self._get_stop_phrase()
        return re.compile(rf"\b{re.escape(stop_phrase)}\b", re.IGNORECASE)

    async def monitor_stop_words(self, telegram_id: int, response_message: str) -> str:
        """
        Проверяет сообщение на наличие стоп-фраз и при их обнаружении завершает исследование.

        :param telegram_id: ID исследования, для которого выполняется проверка.
        :param response_message: Проверяемое сообщение (сгенерированное или полученное в процессе исследования).
        :return: True, если была обнаружена стоп-фраза и исследование завершено, иначе False.
        """
        try:
            pattern = await self._get_stop_pattern()

            if not self._is_contains_stop_phrase(message=response_message, pattern=pattern):
                return response_message

            logger.info(f"Найдена стоп-фраза в сообщении для исследования {telegram_id}: '{response_message}'")

            cleared_message = await self._delete_stop_word(message=response_message, pattern=pattern)
            await self.repo.user_in_research_repo.short.update_user_status(telegram_id, UserStatusEnum.DONE)
            return cleared_message

        except Exception as e:
            logger.error(f"Ошибка при проверке стоп-слов для исследования у пользователя {telegram_id}: {str(e)}")
            raise

    # TODO refactor
    @async_wrap
    def _delete_stop_word(self, message: str, pattern: Pattern) -> str:
        try:
            return re.sub(pattern, "", message)
        except Exception as e:
            logger.error("Ошибка в удалении стоп слова")
            raise e

    def _is_contains_stop_phrase(self, message: str, pattern: Pattern) -> bool:
        """
        Выполняет поиск стоп-слов в сообщении с использованием регулярных выражений.
        :param message: Сообщение для проверки.
        :return: True, если найдена стоп-фраза, иначе False.
        """
        return pattern.search(message) is not None


class PingDelayCalculator:
    def __init__(self):
        # Используем лучше читаемое присваивание
        self.table: Dict[int, int] = research_pingator_settings.ping_delay.table or self._load_table()

    @staticmethod
    def _load_table() -> Dict[int, int]:
        return {1: 1, 2: 6, 3: 24, 4: 48, 5: 72, 6: 100}

    def calculate(self, n: int) -> int:
        """Рассчитывает задержку пинга, используя таблицу для n <= 6 и формулу для n > 6."""
        if n < 0:
            logger.warning("Input value of n must be non-negative. Returning 0.")
            return 0
        elif n in self.table:
            return self.table[n]
        else:
            return int(math.ceil(10 * math.log(n) * (n - 3) + 24))


class UserPingator:
    def __init__(self, repo, publisher):
        self.repo = repo
        self.publisher = publisher
        self._attempt_calculator = CyclePingAttemptCalculator
        self._ping_calculator = PingDelayCalculator()

    async def get_config(self) -> ConfigurationSchema:
        return await self.repo.configuration_repo.get()

    async def ping_users(self, research_id: int):
        """Пинг пользователей до тех пор, пока есть активные пользователи."""
        logger.info(f"Start ping for research {research_id} ")

        research_info: ResearchDTOFull = await self.repo.research_repo.short.get_research_by_id(research_id=research_id)
        config = await self.get_config()
        logger.debug(f"________________CONFIG {config}")

        while True:
            users = await self.get_active_users(research_id)
            await self.ping_users_concurrently(users, research_info)
            await asyncio.sleep(config.ping_interval)

    async def ping_users_concurrently(self, users: List[UserDTOFull], research_info: ResearchDTOFull):
        """Пингует пользователей параллельно с обработкой исключений."""
        tasks = [self.handle_user_ping(user, research_info) for user in users]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Ошибка пинга пользователя: {str(result)}")

    async def handle_user_ping(self, user: UserDTOFull, research_info: ResearchDTOFull):
        """Обработка пинга для одного пользователя."""
        try:
            unresponded_messages = await self.count_unresponded_assistant_message(
                telegram_id=user.tg_user_id,
                research_id=research_info.research_id,
                telegram_client_id=research_info.telegram_client_id,
                assistant_id=research_info.assistant_id,
            )

            if unresponded_messages == 0:
                return

            config = await self.get_config()
            if unresponded_messages > config.ping_max_messages:
                return

            time_delay = self._ping_calculator.calculate(n=unresponded_messages)
            # TODO Добавить переменные
            send_time = await self.calculate_send_time(
                telegram_id=user.tg_user_id,
                research_id=research_info.research_id,
                telegram_client_id=research_info.telegram_client_id,
                assistant_id=research_info.assistant_id,
                time_delay=time_delay,
            )

            # Время в UTC стандарте
            current_time_utc = datetime.now(pytz.utc)

            if send_time and send_time <= current_time_utc:
                await self.send_command_message_ping_user(
                    user=user, message_number=unresponded_messages, research_id=research_info.research_id
                )

        except Exception as e:
            logger.error(f"Ошибка в обработке пинга для пользователя {user.tg_user_id}: {str(e)}")

    # TODO
    async def send_command_message_ping_user(self, user: UserDTOFull, message_number: int, research_id: int):
        """Отправка пинг-сообщения."""

        user_queue_dto = UserDTQueue(name=str(user.username), tg_user_id=str(user.tg_user_id))
        message_dto = PingDataQueueDTO(
            user=user_queue_dto.dict(), message_number=str(message_number), research_id=str(research_id)
        )
        subject_message: NatsQueueMessageDTOSubject = NatsQueueMessageDTOSubject(
            message=message_dto.model_dump_json(serialize_as_any=True),
            subject=nats_subscriber_communicator_settings.commands.ping_user,
        )

        try:
            await self.publisher.publish_message_to_subject(subject_message=subject_message)
            logger.info(f"Отправил в паблишер сообщение {subject_message}")

        except Exception as e:
            logger.error(f"Ошибка при отправке пинг-сообщения: {str(e)}")

    # TODO: Возможно добавить повторные попытки отправки или логику алертинга

    async def get_research_current_status(self, research_id: int) -> str:
        research_status = await self.repo.status_repo.research_status.get_research_status(research_id=research_id)
        if research_status:
            return research_status.status_name
        raise ValueError("No status name value")

    async def count_unresponded_assistant_message(
        self, telegram_id: int, research_id: int, telegram_client_id: int, assistant_id: int
    ) -> int:
        """Получение всех неотвеченных сообщений от ассистента."""
        unresponded_messages = await self.repo.message_repo.assistant.fetch_context_assistant_messages_after_user(
            telegram_id=telegram_id,
            research_id=research_id,
            telegram_client_id=telegram_client_id,
            assistant_id=assistant_id,
        )

        return len(unresponded_messages)

    async def calculate_send_time(
        self, telegram_id: int, research_id: int, telegram_client_id: int, assistant_id: int, time_delay: int
    ) -> Optional[datetime]:
        """Расчёт времени отправки следующего пинга."""
        try:
            last_message = await self.repo.message_repo.user.get_last_user_message_in_context_by_user_telegram_id(
                telegram_id, research_id, telegram_client_id, assistant_id
            )
            # Конвертируем точно в UTC
            if not last_message:
                last_message = (
                    await self.repo.message_repo.assistant.get_last_assistant_message_in_context_by_user_telegram_id(
                        telegram_id, research_id, telegram_client_id, assistant_id
                    )
                )

            if last_message:
                last_message_time = (
                    last_message.created_at.replace(tzinfo=pytz.utc)
                    if last_message.created_at.tzinfo is None
                    else last_message.created_at.astimezone(pytz.utc)
                )
                # TODO сделать изменение атрибута секунды часы минуты
                return last_message_time + timedelta(hours=time_delay)
            else:
                return

        except Exception as e:
            logger.error("Error with calculation time send time")
            raise e

    async def get_active_users(self, research_id) -> List[UserDTOFull]:
        """Получение пользователей со статусом IN_PROGRESS."""
        return await self.repo.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )


class ResearchProcess:
    def __init__(
        self,
        repository: RepoStorage,
        publisher: NatsPublisher,
        notifier=None,
    ):
        self.research_starter = ResearchStarter(repository=repository, publisher=publisher)
        self.research_stopper = ResearchStopper(repository, notifier)
        self.research_banner = ResearchBanner(repository=repository, publisher=publisher)
        self.user_status_stopper = UserDoneStopper(repository=repository, stopper=self.research_stopper)
        self.research_status_stopper = ResearchStatusStopper(repository=repository, stopper=self.research_stopper)
        self.research_over_checker = ResearchOverChecker(repository, self.research_stopper)
        self.research_user_pingator = UserPingator(repo=repository, publisher=publisher)

        # Словарь для хранения задач
        self._tasks: Dict[int, List[Task]] = {}

    async def run(self, research_id: int) -> int:
        """
        Запуск основного цикла проведения исследования.
        """
        await self.research_starter.start_up_research(research_id)
        return await self._start_tasks(research_id)

    async def ban(
            self,
            research_id: int,
    ) -> None:
        """
        Приостановить исследование, остановив все связанные задачи.
        """
        logger.info(f"Приостанавливаю исследование {research_id}.")
        self._cancel_pending_tasks(research_id)
        await self.research_banner.ban_research(research_id=research_id)

    async def unban(
            self,
            research_id: int,
    ) -> int:
        """
        Возобновление выполнения исследования.
        """
        logger.info(f"Возобновляю выполнение исследования {research_id}.")
        await self.research_banner.unban_research(research_id)
        return await self._start_tasks(research_id)

    async def _start_tasks(self, research_id: int) -> int:
        """
        Общий метод для запуска задач исследования.
        """
        # Проверяем, если задачи уже запущены
        if research_id in self._tasks:
            logger.warning(f"Исследование {research_id} уже запущено.")
            return 0

        # Создаём и сохраняем задачи
        self._tasks[research_id] = self._create_tasks(research_id)
        logger.info(f"Задачи исследования {research_id} запущены.")

        try:
            # Ожидание завершения одной из задач
            done, pending = await asyncio.wait(
                self._tasks[research_id],
                return_when=asyncio.FIRST_COMPLETED,
            )

            logger.info(f"Завершены задачи: {len(done)}. Отменяю оставшиеся задачи.")
            logger.info(f"Done tasks: {done}")
            self._cancel_pending_tasks(research_id, pending)

            # Если задачи отменены или выбросили ошибку, то исследование не завершено
            for task in done:
                if task.cancelled():
                    logger.info(f"Задача {task} была отменена.")
                    return 0
                elif task.exception():
                    logger.error(f"Ошибка в задаче {task}: {task.exception()}")
                    return 0  #

            # Завершаем исследование
            await self.research_stopper.complete_research(research_id)
            logger.info(f"Все задачи исследования {research_id} завершены.")

            # Отмена запланированных задач по этому исследованию
            await self._cancel_scheduled_messages(research_id)
            logger.info(f"Все задачи исследования {research_id} завершены.")

            return 1

        except Exception as e:
            logger.error(f"Ошибка в процессе исследования {research_id}: {str(e)}")
            # Завершаем исследование
            self._cancel_pending_tasks(research_id)

            # Отмена запланированных задач по этому иследованию
            await self._cancel_scheduled_messages(research_id)
            raise e


    def _create_tasks(self, research_id: int) -> list[Task]:
        """Создаёт список задач для исследования."""
        return [
            asyncio.create_task(self.research_over_checker.monitor_time_completion(research_id)),
            asyncio.create_task(self.user_status_stopper.monitor_user_status(research_id)),
            asyncio.create_task(self.research_status_stopper.monitor_research_status(research_id)),
            asyncio.create_task(self.research_user_pingator.ping_users(research_id)),
        ]

    def _cancel_pending_tasks(
            self,
            research_id: int,
            tasks: Optional[List[Task]]=None
    ) -> None:
        """
        Отменяет все задачи исследования
        """
        if research_id not in self._tasks:
            logger.info(f"Задачи для исследования {research_id} не найдены.")
            return

        tasks_to_cancel = tasks or self._tasks[research_id]
        for task in tasks_to_cancel:
            task.cancel()
            logger.info(f"Задача {task} отменена.")

        # Удаляем задачи из словаря
        if not tasks:
            del self._tasks[research_id]

    @staticmethod
    async def _cancel_scheduled_messages(
            research_id: int,
    )->None:
        """
        Отменяет все запланированые таски по первому сообщению
        """
        schedular = AsyncRedisApschedulerManager()
        schedular.start()
        try:
            schedular.start()
            await schedular.delete_scheduled_task(prefix=f'first_message:research:{research_id}')
            logger.debug(f"Задачи отменена")

        except Exception as e:
            logger.error(f"Ошибка завершения запланированных работ")
            raise e

        finally:
            schedular.shutdown()
            del schedular
            logger.debug(f"Объект планировщика удален")
