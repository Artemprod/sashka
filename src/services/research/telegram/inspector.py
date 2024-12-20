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
import pytz
from loguru import logger
from mako.testing.helpers import result_lines

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
from src.services.exceptions.research import UntimelyCompletionError, ResearchCompletionError, \
    UserAndResearchInProgressError, UserInProgressError, ResearchStatusInProgressError
from src.services.publisher.publisher import NatsPublisher
from src.services.research.models import PingDataQueueDTO
from src.services.research.telegram.decorators.finish_reserch import move_users_to_archive
from src.services.research.utils import CyclePingAttemptCalculator
from src.utils.wrappers import async_wrap


#TODO Вынести во всех классах reserch id в инициализхатор классса потому что классы являются частю фасада
class BaseStopper:

    def __init__(self, repository, stopper):
        self.repository = repository
        self.stopper = stopper
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, int]:
        return {"delay_check_interval": 60}

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

        logger.info(f"Исследование {research_id} завершено успешно")
        return 1



    async def _update_research_status(self, research_id: int) -> None:
        """Обновление статуса исследования."""
        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id, status=ResearchStatusEnum.DONE
        )
        logger.info(f"Статус исследования {research_id} обновлён на DONE")

    async def _update_user_statuses(self, user_group: List[UserDTOFull]) -> None:
        """Обновление статусов пользователей."""
        await self.repository.status_repo.user_status.update_status_group_of_user(
            user_group=user_group,
            status=UserStatusEnum.DONE
        )
        logger.info(f"Статусы пользователей в группе {user_group} обновлены на DONE")

    async def _get_users_in_research(self, research_id) -> List[UserDTOFull]:
        users_in_research = await self.repository.user_in_research_repo.short.get_users_by_research_id(
            research_id=research_id
        )
        return [user.tg_user_id for user in users_in_research]

    async def _get_users_in_progress(self, research_id) -> int:
        users_in_progress = await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id,
            status=UserStatusEnum.IN_PROGRESS
        )
        return len(users_in_progress)

    async def _get_research_status(self, research_id: int) -> ResearchStatusEnum:
        """Получение текущего статуса исследования."""
        research_status = await self.repository.status_repo.research_status.get_research_status(
            research_id=research_id
        )
        return research_status.status_name

class UserDoneStopper(BaseStopper):

    async def monitor_user_status(self,research_id:int)->int:
        while True:
            # Проверка наличие активных пользователей
            users_in_progress = await self._get_users_in_progress(research_id)
            if not users_in_progress:
                logger.info(f"Завершаю исследование {research_id}, так как закончились пользователи")
                return 1

            logger.info(f"Проверяю исследование {research_id}, пользователей в процессе: {users_in_progress}")
            await asyncio.sleep(self.settings['delay_check_interval'])

    async def _get_users_in_progress(self, research_id: int)->int:
        # Получение пользователей с активным статусом
        users_in_progress = await self.repository.user_in_research_repo.short.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS)
        return len(users_in_progress)

class ResearchStatusStopper(BaseStopper):

    async def monitor_research_status(self, research_id:int)->int:

        while True:
            research_status = await self._get_research_current_status(research_id)
            # Проверка на смену статуса исследования
            if research_status not in [ResearchStatusEnum.IN_PROGRESS.value, ResearchStatusEnum.WAIT.value]:
                logger.info(f"Завершаю исследование {research_id} по смене статуса. Статус {research_status}")
                return 1

            logger.info(f"Проверяю исследование {research_id}, статус исследования: {research_status}")
            await asyncio.sleep(self.settings['delay_check_interval'])

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

            print("CURRENT TIME ____ ",current_time)
            print("END DATE ____ ", end_date)

            # Проверка на конечную дату
            if current_time >= end_date:
                logger.info(f"Завершаю исследование {research_id} по истечению времени, время завершения {current_time}")
                return 1

            logger.info(
                f"Проверяю исследование {research_id}, оставшееся время иследвония : {end_date - current_time}")

            await asyncio.sleep(self.settings['delay_check_interval'])

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
    """Класс для поиска как точного, так и частичного стоп-слов в сообщениях, завершение исследования при их нахождении."""

    def __init__(self,
                 repo: 'RepoStorage',
                 stop_phrases: Optional[str] = None):
        """
        :param stopper: Объект класса ResearchStopper, который выполняет завершение исследования.
        :param repo: Репозиторий для работы с данными.
        :param stop_phrases: Cтоп-фраза для проверки. Если не передан, используются стандартная фраза.
        """
        self.repo = repo
        self.stop_phrase = stop_phrases or 'STOP_DIALOG'
        self.stop_pattern = re.compile(rf'\b{re.escape(self.stop_phrase)}\b', re.IGNORECASE)

    async def monitor_stop_words(self, telegram_id: int, response_message: str) -> str:
        """
        Проверяет сообщение на наличие стоп-фраз и при их обнаружении завершает исследование.

        :param telegram_id: ID исследования, для которого выполняется проверка.
        :param response_message: Проверяемое сообщение (сгенерированное или полученное в процессе исследования).
        :return: True, если была обнаружена стоп-фраза и исследование завершено, иначе False.
        """
        try:
            if not await self._contains_stop_phrase(response_message):
                return response_message

            logger.info(f"Найдена стоп-фраза в сообщении для исследования {telegram_id}: '{response_message}'")
            cleared_message =  await self._delete_stop_word(response_message)
            await self.repo.user_in_research_repo.short.update_user_status(telegram_id, UserStatusEnum.DONE)
            return cleared_message

        except Exception as e:
            logger.error(f"Ошибка при проверке стоп-слов для исследования у пользователя {telegram_id}: {str(e)}")
            raise

    # TODO refactor
    @async_wrap
    def _delete_stop_word(self, message: str) -> str:
        try:
            result = re.sub(self.stop_pattern, "", message)
            return result
        except Exception as e:
            logger.error("Ошибка в удалении стоп слова")
            raise e


    async def _contains_stop_phrase(self, message: str) -> bool:
        """
        Выполняет поиск стоп-слов в сообщении с использованием регулярных выражений.
        :param message: Сообщение для проверки.
        :return: True, если найдена стоп-фраза, иначе False.
        """
        return self.stop_pattern.search(message) is not None


    async def update_stop_phrases(self, new_word: str):
        """
        Обновляет список стоп-фраз и пересоздает регулярные выражения для нового набора фраз.

        :param new_word: Новый список стоп-фраз.
        """
        self.stop_phrase = new_word
        self.stop_pattern = re.compile(rf'\b{re.escape(self.stop_phrase)}\b', re.IGNORECASE)
        logger.info("Стоп-фраза обновлена")

    async def log_stop_phrases(self):
        """Логирует текущий список стоп-фраз."""
        logger.info(f"Текущая стоп-фраза: {self.stop_phrase}")


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

        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, int]:
        return {"delay_check_interval": 60}

    async def ping_users(self, research_id: int):
        """Пинг пользователей до тех пор, пока есть активные пользователи."""
        logger.info(f"Start ping for research {research_id} ")

        research_info: ResearchDTOFull = await self.repo.research_repo.short.get_research_by_id(research_id=research_id)

        while True:
            users = await self.get_active_users(research_id)
            await self.ping_users_concurrently(users, research_info)
            await asyncio.sleep(self.config.ping_interval)


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
            unresponded_messages = await self.count_unresponded_assistant_message(telegram_id=user.tg_user_id,
                                                                                  research_id=research_info.research_id,
                                                                                  telegram_client_id=research_info.telegram_client_id,
                                                                                  assistant_id=research_info.assistant_id)
            print("______________UNREPOND_MESSAGES__________",unresponded_messages)
            if unresponded_messages == 0:
                return

            if unresponded_messages > self.config.max_pings_messages:
                logger.info(f"Превышено максимальное количество пингов для пользователя {user.tg_user_id}.")
                return

            time_delay = self._ping_calculator.calculate(n=unresponded_messages)
            send_time = await self.calculate_send_time(telegram_id=user.tg_user_id,
                                                       research_id=research_info.research_id,
                                                       telegram_client_id=research_info.telegram_client_id,
                                                       assistant_id=research_info.assistant_id,
                                                       time_delay=time_delay)

            # Время в UTC стандарте
            current_time_utc = datetime.now(pytz.utc)


            if send_time and send_time <= current_time_utc:
                await self.send_command_message_ping_user(user=user,
                                                          message_number=unresponded_messages,
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


    async def count_unresponded_assistant_message(self, telegram_id: int,research_id:int, telegram_client_id:int, assistant_id:int) -> int:
        """Получение всех неотвеченных сообщений от ассистента."""
        unresponded_messages = await self.repo.message_repo.assistant.fetch_context_assistant_messages_after_user(
            telegram_id=telegram_id,
            research_id=research_id,
            telegram_client_id=telegram_client_id,
            assistant_id=assistant_id)

        print("НЕОТВЕЧЕНЫЕ СООБЩЕНИЯ_____________",len(unresponded_messages)," ", unresponded_messages)
        return len(unresponded_messages)

    async def calculate_send_time(self, telegram_id: int,research_id:int, telegram_client_id:int, assistant_id:int, time_delay: int) -> Optional[datetime]:
        """Расчёт времени отправки следующего пинга."""
        try:
            last_message = await self.repo.message_repo.user.get_last_user_message_in_context_by_user_telegram_id(telegram_id,
                                                                                                                       research_id,
                                                                                                                       telegram_client_id,
                                                                                                                       assistant_id)
            # Конвертируем точно в UTC
            if not last_message:
                last_message = await self.repo.message_repo.assistant.get_last_assistant_message_in_context_by_user_telegram_id(
                    telegram_id,
                    research_id,
                    telegram_client_id,
                    assistant_id)

            if last_message:
                last_message_time = (
                    last_message.created_at.replace(tzinfo=pytz.utc)
                    if last_message.created_at.tzinfo is None
                    else last_message.created_at.astimezone(pytz.utc)
                )
                #TODO сделать изменение атрибута секунды часы минуты
                return last_message_time + timedelta(hours=time_delay)
            else:return

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
                 publisher: NatsPublisher,
                 notifier=None,
                 ):


        self.research_starter = ResearchStarter(repository=repository, publisher=publisher)
        self.research_stopper = ResearchStopper(repository, notifier)
        self.user_status_stopper = UserDoneStopper(repository=repository, stopper=self.research_stopper)
        self.research_status_stopper = ResearchStatusStopper(repository=repository, stopper=self.research_stopper)
        self.research_over_checker = ResearchOverChecker(repository, self.research_stopper)
        self.research_user_pingator = UserPingator(repo=repository, publisher=publisher)

    async def run(self, research_id: int) -> int:
        """ Основной цикл проведения исследования. """
        await self.research_starter.start_up_research(research_id)

        # Запуск асинхронных задач для проверки завершения исследования

        tasks_over_checker = asyncio.create_task(self.research_over_checker.monitor_time_completion(research_id))
        task_user_done_status = asyncio.create_task(self.user_status_stopper.monitor_user_status(research_id))
        task_research_done_status = asyncio.create_task(self.research_status_stopper.monitor_research_status(research_id))
        tasks_user_ping = asyncio.create_task(self.research_user_pingator.ping_users(research_id))

        try:
            # Ждём, когда одна из задач завершится, остальные будут отменены
            done, pending = await asyncio.wait([tasks_over_checker,
                                                task_user_done_status,
                                                task_research_done_status,
                                                tasks_user_ping],

                                               return_when=asyncio.FIRST_COMPLETED)

            logger.info(f"pending tasks {len(pending)}")
            # Отмена всех оставшихся задач (например, пингатор может продолжать дольше нужного)
            for task in pending:
                task.cancel()
            logger.info(f'All tasks stoped')

            # Проверяем и заврешаем иследование
            await self.research_stopper.complete_research(research_id)

            logger.info(f'Все задачи исследования {research_id} завершены.')
            return 1

        except Exception as e:
            # Обработка ошибок на глобальном уровне
            logger.error(f"Ошибка в процессе исследования {research_id}: {str(e)}")
            raise e


