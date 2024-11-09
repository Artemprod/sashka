import asyncio
import json
import math
import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Dict
from typing import List
from typing import Optional

from loguru import logger

from configs.nats_queues import nats_subscriber_communicator_settings
from configs.research import research_pingator_settings
from src.database.postgres.models.enum_types import ResearchStatusEnum
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.repository.storage import RepoStorage
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.schemas.service.research import ResearchDTOFull
from src.schemas.service.user import UserDTOBase
from src.schemas.service.user import UserDTOFull
from src.schemas.service.user import UserDTQueue
from src.services.publisher.publisher import NatsPublisher
from src.services.research.models import PingDataQueueDTO
from src.services.research.utils import CyclePingAttemptCalculator


class ResearchStarter:
    def __init__(self,
                 repository: RepoStorage,
                 publisher: NatsPublisher):

        self.repository = repository
        self.publisher = publisher
        self.settings = self._load_seatings()

    def _load_seatings(self):
        return {
            "command_subject": "command.dialog.start"
        }

    async def start_up_research(self, research_id: int) -> None:
        """ Начинает исследование, разослав сообщения пользователям. """

        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id, status=ResearchStatusEnum.IN_PROGRESS
        )
        user_group: List[UserDTOFull] = await self._get_users_in_research(research_id)

        await self.repository.status_repo.user_status.update_status_group_of_user(
            user_group=[user.tg_user_id for user in user_group], status=UserStatusEnum.IN_PROGRESS
        )
        users_dto = [UserDTOBase(username=user.username, tg_user_id=user.tg_user_id).dict() for user in user_group]
        await self._publish_star_dialog_command(users=users_dto, research_id=research_id)

        logger.info("Команда отправлена ")

    async def _publish_star_dialog_command(self, users: List[dict], research_id: int):
        subject_message: NatsQueueMessageDTOSubject = NatsQueueMessageDTOSubject(
            message="",
            subject=self.settings['command_subject'],
            headers={"users": json.dumps(users),
                     "research_id": str(research_id)},
        )
        try:
            await self.publisher.publish_message_to_subject(subject_message=subject_message)
        except Exception as e:
            raise e

    async def _get_users_in_research(self, research_id) -> List[UserDTOFull]:
        users_in_research: List[
            UserDTOFull] = await self.repository.user_in_research_repo.short.get_users_by_research_id(
            research_id=research_id
        )
        return users_in_research


class ResearchStopper:
    def __init__(self,
                 repository: RepoStorage,
                 notifier):
        self.repository = repository
        self.notifier = notifier

    async def complete_research(self, research_id) -> None:
        """ Останавливает исследование и переводит его статус на завершённый """
        user_group = await self._get_users_in_research(research_id)
        logger.info('Начал завершение исследования')

        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id, status=ResearchStatusEnum.DONE
        )

        await self.repository.status_repo.user_status.update_status_group_of_user(
            user_group=user_group, status=UserStatusEnum.DONE
        )

        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        user_in_progress = await self._get_users_in_progress(research_id=research_id)

        if research_status.status_name != ResearchStatusEnum.IN_PROGRESS and not user_in_progress:
            logger.info("Исследование завершено")
            # await self.notifier.notify_completion()

        else:
            logger.info("Исследование не завершено")
            logger.info(
                f"Статус исследования: {research_status.status_name}, Пользователи в процессе: {len(user_in_progress)}")
            # await self.notifier.handle_incomplete_research()

    async def _get_users_in_research(self, research_id) -> List[UserDTOFull]:
        users_in_research = await self.repository.user_in_research_repo.short.get_users_by_research_id(
            research_id=research_id
        )
        return [user.tg_user_id for user in users_in_research]

    async def _get_users_in_progress(self, research_id):
        return await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )


class ResearchOverChecker:
    def __init__(self, repository, stopper):
        self.repository = repository
        self.stopper = stopper
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, int]:
        return {"delay_check_interval": 60}

    async def monitor_completion(self, research_id: int):
        """
        Универсальный метод для проверки завершения исследования (по времени
        или по статусу пользователей). Проверяет на двух уровнях: по энд-дате и
        по количеству пользователей в процессе.
        """
        end_date = await self._get_research_end_date(research_id)

        while True:
            research_status = await self.get_research_current_status(research_id)

            # Проверка на конечную дату
            if end_date and datetime.now() >= end_date:
                await self.stopper.complete_research(research_id)
                logger.info(f"Завершил исследование {research_id} по истечению времени")
                break

            # Проверка на наличие активных пользователей
            user_in_progress = await self._get_users_in_progress(research_id)

            if not user_in_progress:
                await self.stopper.complete_research(research_id)
                logger.info(f"Завершил исследование {research_id}, так как закончились пользователи")
                break

            # Проверка на смену статуса исследования
            if research_status not in [ResearchStatusEnum.IN_PROGRESS.value, ResearchStatusEnum.WAIT.value]:
                await self.stopper.complete_research(research_id)
                logger.info(f"Завершил исследование {research_id} по смене статуса")
                break

            logger.info(f"Проверяю исследование {research_id}, пользователей в процессе: {len(user_in_progress)}")
            await asyncio.sleep(self.settings['delay_check_interval'])

    async def _get_research_end_date(self, research_id: int) -> Optional[datetime]:
        research = await self.repository.research_repo.short.get_research_by_id(research_id=research_id)
        return research.end_date.replace(tzinfo=None) if research.end_date else None

    async def _get_users_in_progress(self, research_id: int) -> List[UserDTOFull]:
        # Получение пользователей с активным статусом
        return await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )

    async def get_research_current_status(self, research_id: int) -> str:
        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        return research_status.status_name


class StopWordChecker:
    """Класс для поиска как точного, так и частичного стоп-слов в сообщениях, завершение исследования при их нахождении."""

    def __init__(self,
                 stopper: 'ResearchStopper',
                 repo: 'RepoStorage',
                 stop_phrases: Optional[List[str]] = None):
        """
        :param stopper: Объект класса ResearchStopper, который выполняет завершение исследования.
        :param repo: Репозиторий для работы с данными.
        :param stop_phrases: Список стоп-фраз для проверки. Если не передан, используются стандартные фразы.
        """
        self.stopper = stopper
        self.repo = repo
        self.stop_phrases = stop_phrases or ["завершено", "исследование завершено", "конец исследования", "окончено",
                                             "STOP"]
        self.stop_patterns = [re.compile(rf'\b{re.escape(phrase)}\b', re.IGNORECASE) for phrase in self.stop_phrases]

    async def check_for_stop_words(self, research_id: int, response_message: str) -> bool:
        """
        Проверяет сообщение на наличие стоп-фраз и при их обнаружении завершает исследование.

        :param research_id: ID исследования, для которого выполняется проверка.
        :param response_message: Проверяемое сообщение (сгенерированное или полученное в процессе исследования).
        :return: True, если была обнаружена стоп-фраза и исследование завершено, иначе False.
        """
        try:
            if await self._contains_stop_phrase(response_message) or await self.check_partial_match(response_message):
                logger.info(f"Найдена стоп-фраза в сообщении для исследования {research_id}: '{response_message}'")

                await self.stopper.complete_research(research_id=research_id)
                return True
            return False

        except Exception as e:
            logger.error(f"Ошибка при проверке стоп-слов для исследования {research_id}: {str(e)}")
            return False

    async def _contains_stop_phrase(self, message: str) -> bool:
        """
        Выполняет поиск стоп-слов в сообщении с использованием регулярных выражений.
        :param message: Сообщение для проверки.
        :return: True, если найдена стоп-фраза, иначе False.
        """
        return any(pattern.search(message) for pattern in self.stop_patterns)

    async def check_partial_match(self, message: str, threshold: float = 0.8) -> bool:
        """
        Проверяет частичное совпадение стоп-фраз в сообщении.

        :param message: Сообщение для проверки.
        :param threshold: Пороговое значение для частичного совпадения (по умолчанию 0.8 или 80%).
        :return: True, если частичное совпадение превышает порог, иначе False.
        """
        words = message.lower().split()
        for phrase in self.stop_phrases:
            phrase_words = phrase.lower().split()  # Разбиваем фразу на слова
            matches = sum(word in words for word in phrase_words)  # Подсчитываем совпавшие слова
            if matches / len(phrase_words) >= threshold:
                return True
        return False

    async def update_stop_phrases(self, new_phrases: List[str]):
        """
        Обновляет список стоп-фраз и пересоздает регулярные выражения для нового набора фраз.

        :param new_phrases: Новый список стоп-фраз.
        """
        self.stop_phrases = new_phrases
        self.stop_patterns = [re.compile(rf'\b{re.escape(phrase)}\b', re.IGNORECASE) for phrase in self.stop_phrases]
        logger.info("Список стоп-фраз обновлен")

    async def log_stop_phrases(self):
        """Логирует текущий список стоп-фраз."""
        logger.info(f"Текущий список стоп-фраз: {', '.join(self.stop_phrases)}")


class PingDelayCalculator:
    def __init__(self):
        # Используем лучше читаемое присваивание
        self.table: Dict[int, int] = research_pingator_settings.ping_delay.table or self._load_table()

    @staticmethod
    def _load_table() -> Dict[int, int]:
        return {1: 1, 2: 6, 3: 24, 4: 48, 5: 72, 6: 100}

    def calculate(self, n: int) -> int:
        """ Рассчитывает задержку пинга, используя таблицу для n <= 6 и формулу для n > 6. """
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
        self.config = research_pingator_settings
        self._attempt_calculator = CyclePingAttemptCalculator
        self._ping_calculator = PingDelayCalculator()

    async def ping_users(self, research_id: int):
        """Пинг пользователей до тех пор, пока есть активные пользователи."""
        logger.info(f"Start ping for research {research_id} ")

        research_info: ResearchDTOFull = await self.repo.research_repo.short.get_research_by_id(research_id=research_id)
        max_attempt = self._attempt_calculator(
            research_info=research_info,
            attempt_multiplicative=self.config.ping_attempts_multiplier).calculate_max_attempts()

        attempt = 0
        while attempt < max_attempt:
            users = await self.get_active_users(research_id)
            research_status = await self.get_research_current_status(research_id)

            # Объединенные проверки завершения
            if not users or research_status not in [ResearchStatusEnum.IN_PROGRESS.value,
                                                    ResearchStatusEnum.WAIT.value]:
                logger.info("Все пользователи завершили задачи либо исследование неактивно. Остановка пинга.")
                break

            await self.ping_users_concurrently(users, research_info)
            await asyncio.sleep(self.config.ping_interval)
            attempt += 1

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
            unresponded_messages = await self.count_unresponded_assistant_message(user.tg_user_id)
            if unresponded_messages == 0:
                return

            if unresponded_messages > self.config.max_pings_messages:
                logger.info(f"Превышено максимальное количество пингов для пользователя {user.tg_user_id}.")
                return
            time_delay = self._ping_calculator.calculate(n=unresponded_messages)
            send_time = await self.calculate_send_time(user.tg_user_id, time_delay)
            current_time_utc = datetime.now(timezone.utc)

            if send_time <= current_time_utc:
                await self.send_command_message_ping_user(user=user, message_number=unresponded_messages,
                                                          research_id=research_info.research_id)

        except Exception as e:
            logger.error(f"Ошибка в обработке пинга для пользователя {user.tg_user_id}: {str(e)}")

    # TODO
    async def send_command_message_ping_user(self, user: UserDTOFull, message_number: int, research_id: int):
        """Отправка пинг-сообщения."""

        user_queue_dto = UserDTQueue(name=str(user.username), tg_user_id=str(user.tg_user_id))
        message_dto = PingDataQueueDTO(user=user_queue_dto.dict(),
                                       message_number=str(message_number),
                                       research_id=str(research_id))
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

    async def count_unresponded_assistant_message(self, telegram_id: int) -> int:
        """Получение всех неотвеченных сообщений от ассистента."""
        unresponded_messages = await self.repo.message_repo.assistant.fetch_assistant_messages_after_user(
            telegram_id=telegram_id)
        return len(unresponded_messages)

    async def calculate_send_time(self, telegram_id: int, time_delay: int) -> datetime:
        """Расчёт времени отправки следующего пинга."""
        try:
            last_user_message = await self.repo.message_repo.user.get_last_user_message_by_user_telegram_id(telegram_id)
            # TODO поменять потом на часасы секунды
            last_message_time = last_user_message.created_at.replace(
                tzinfo=timezone.utc) if last_user_message.created_at.tzinfo is None else last_user_message.created_at
            return last_message_time + timedelta(seconds=time_delay)
        except Exception as e:
            logger.error("Error with calculation time send time")
            raise e

    async def get_active_users(self, research_id) -> List[UserDTOFull]:
        """Получение пользователей со статусом IN_PROGRESS."""
        return await self.repo.user_in_research_repo.short.get_users_by_research_with_status(research_id=research_id,
                                                                                             status=UserStatusEnum.IN_PROGRESS)


class ResearchProcess:
    def __init__(self,
                 repository: RepoStorage,
                 notifier,
                 publisher: NatsPublisher,
                 ):

        self.research_starter = ResearchStarter(repository=repository, publisher=publisher)
        self.research_stopper = ResearchStopper(repository, notifier)
        self.research_over_checker = ResearchOverChecker(repository, self.research_stopper)
        self.research_user_pingator = UserPingator(repo=repository, publisher=publisher)

    async def run(self, research_id: int) -> None:
        """ Основной цикл проведения исследования. """
        await self.research_starter.start_up_research(research_id)

        # Запуск асинхронных задач для проверки завершения исследования

        tasks_over_checker = asyncio.create_task(self.research_over_checker.monitor_completion(research_id))
        tasks_user_ping = asyncio.create_task(self.research_user_pingator.ping_users(research_id))

        try:
            # Ждём, когда одна из задач завершится, остальные будут отменены
            done, pending = await asyncio.wait([tasks_over_checker, tasks_user_ping],
                                               return_when=asyncio.FIRST_COMPLETED)

            # Отмена всех оставшихся задач (например, пингатор может продолжать дольше нужного)
            for task in pending:
                task.cancel()

            logger.info(f'Все задачи исследования {research_id} завершены.')
        except Exception as e:
            # Обработка ошибок на глобальном уровне
            logger.error(f"Ошибка в процессе исследования {research_id}: {str(e)}")
            raise e
