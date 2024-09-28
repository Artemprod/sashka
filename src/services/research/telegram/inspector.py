import asyncio
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from faststream.nats import NatsBroker
from loguru import logger

from src.schemas.message import AssistantMessageDTOPost, AssistantMessageDTOGet, UserMessageDTOGet
from src.schemas.queue import NatsQueueMessageDTOStreem, NatsTelegramHeaders
from src.schemas.research import ResearchDTOFull
from src.schemas.user import UserDTOFull
from src.services.publisher.messager import NatsPublisher
from src.services.publisher.notification import TelegramNotificator

from src_v0.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from src_v0.database.postgres.models.message import AssistantMessage
from src_v0.database.repository.storage import RepoStorage
from src_v0.resrcher.open_ai_namager import OpenAiresponser


@dataclass
class PingatorConfig:
    max_pings: int = 4
    ping_attempts: int = 20
    ping_interval: int = 10  # в секундах
    nats_subject = "test.message.conversation.send",
    nast_stream = "CONVERSATION",


class ResearchStarter:
    def __init__(self, repository: RepoStorage, communicator):
        self.repository = repository
        self.communicator = communicator

    async def start_up_research(self, research_id: int) -> None:
        """ Начинает исследование, разослав сообщения пользователям. """
        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id, status=ResearchStatusEnum.IN_PROGRESS
        )
        user_group: List[UserDTOFull] = await self._get_users_in_research(research_id)
        await self.repository.status_repo.user_status.change_status_group_of_user(
            user_group=user_group, status=UserStatusEnum.IN_PROGRESS
        )
        await self.communicator.send_first_message(research_id=research_id)
        logger.info("Все приветственные сообщения отправлены")

    async def _get_users_in_research(self, research_id) -> List[UserDTOFull]:
        users_in_research = await self.repository.user_in_research_repo.short.get_users_by_research_id(
            research_id=research_id
        )
        return [user.tg_user_id for user in users_in_research]


class ResearchStopper:
    def __init__(self, repository: RepoStorage, notifier):
        self.repository = repository
        self.notifier = notifier

    async def complete_research(self, research_id) -> None:
        """ Останавливает исследование и переводит его статус на завершённый """
        user_group = await self._get_users_in_research(research_id)
        logger.info('Начал завершение исследования')

        await self.repository.status_repo.research_status.change_research_status(
            research_id=research_id, status=ResearchStatusEnum.DONE
        )

        await self.repository.status_repo.user_status.change_status_group_of_user(
            user_group=user_group, status=UserStatusEnum.DONE
        )

        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        user_in_progress = await self._get_users_in_progress(research_id=research_id)

        if research_status.status_name != ResearchStatusEnum.IN_PROGRESS and not user_in_progress:
            logger.info("Исследование завершено")
            await self.notifier.notify_completion()
        else:
            logger.info("Исследование не завершено")
            logger.info(
                f"Статус исследования: {research_status.status_name}, Пользователи в процессе: {len(user_in_progress)}")
            await self.notifier.handle_incomplete_research()

    async def _get_users_in_research(self, research_id) -> List[UserDTOFull]:
        users_in_research = await self.repository.user_in_research_repo.short.get_users_by_research_id(
            research_id=research_id
        )
        return [user.tg_user_id for user in users_in_research]

    async def _get_users_in_progress(self, research_id):
        return await self.repository.status_repo.user_status.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )


class ResearchOverChecker:
    def __init__(self, repository, stopper):
        self.repository = repository
        self.stopper = stopper
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, int]:
        # Объединённые настройки для контроля времени и пользователей
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
            if research_status not in [ResearchStatusEnum.IN_PROGRESS, ResearchStatusEnum.WAIT]:
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
        return await self.repository.status_repo.user_status.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )

    async def get_research_current_status(self, research_id: int) -> str:
        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        return research_status.status_name.value


class StopWordChecker:
    """Класс для поиска как точного, так и частичного стоп-слов в сообщениях, завершение исследования при их нахождении."""

    def __init__(self, stopper: 'ResearchStopper',
                 repo: 'RepoStorage',
                 stop_phrases: Optional[List[str]] = None):
        """
        :param stopper: Объект класса ResearchStopper, который выполняет завершение исследования.
        :param repo: Репозиторий для работы с данными.
        :param stop_phrases: Список стоп-фраз для проверки. Если не передан, используются стандартные фразы.
        """
        self.stopper = stopper
        self.repo = repo
        self.stop_phrases = stop_phrases or ["завершено", "исследование завершено", "конец исследования", "окончено", "STOP"]
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
    @staticmethod
    def calculate(n: int) -> int:
        """
        Рассчитывает задержку пинга, используя таблицу для n <= 6 и формулу для n > 6.
        """
        table = {1: 1, 2: 6, 3: 24, 4: 48, 5: 72, 6: 100}

        if n < 0:
            logger.warning("Wrong input, n must be non-negative")
            return 0
        elif n <= 6:
            return table[n]
        else:
            return int(math.ceil(10 * math.log(n) * (n - 3) + 24))


class UserPingator:
    def __init__(self, repo: RepoStorage, communicator: OpenAiresponser, publisher: NatsPublisher,
                 config: PingatorConfig = PingatorConfig()):
        self.repo = repo
        self.communicator = communicator
        self.publisher = publisher
        self.config = config

    async def ping_users(self, research_id: int):
        """Пинг пользователей до тех пор, пока есть активные пользователи."""
        research_info = await self.repo.research_repo.short.get_research_by_id(research_id=research_id)
        attempt = 0

        while attempt < self.config.ping_attempts:
            users = await self.get_active_users(research_id)
            research_status = await self.get_research_current_status(research_id)

            if not users:
                logger.info("Все пользователи завершили задачи. Остановка пинга.")
                break

            if research_status not in [ResearchStatusEnum.IN_PROGRESS, ResearchStatusEnum.WAIT]:
                logger.info("Все пользователи завершили задачи. Остановка пинга.")
                break

            # Параллельная обработка пользователей
            await self.ping_multiple_users(users, research_info)

            await asyncio.sleep(self.config.ping_interval)
            attempt += 1

    async def ping_multiple_users(self, users: List[UserDTOFull], research_info: ResearchDTOFull):
        # Используем asyncio.gather для параллельных пингов с обработкой исключений
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

            if unresponded_messages > self.config.max_pings:
                logger.info(f"Превышено максимальное количество пингов для пользователя {user.tg_user_id}.")
                return

            time_delay = PingDelayCalculator.calculate(unresponded_messages)
            send_time = await self.calculate_send_time(user.tg_user_id, time_delay)

            current_time_utc = datetime.now(timezone.utc)
            if send_time <= current_time_utc:
                await self.send_ping_message(user=user, prompt_number=unresponded_messages, research_info=research_info)
        except Exception as e:
            logger.error(f"Ошибка в обработке пинга для пользователя {user.tg_user_id}: {str(e)}")

    async def send_ping_message(self, user: UserDTOFull, prompt_number: int, research_info: ResearchDTOFull):
        """Отправка пинг-сообщения."""
        try:
            prompt_object = await self.repo.ping_prompt_repo.get_ping_prompt_by_order_number(
                ping_order_number=prompt_number)
            message = await self.communicator.one_message(prompt_object.prompt, prompt_object.system_prompt)

            assistant_message = self.generate_assistant_message_object(message, user, research_info)
            await self.repo.message_repo.assistant.save_new_message(values=assistant_message.dict())

            nats_message = self.generate_nats_message_object(message, user, research_info)
            await self.publisher.publish_message_to_stream(nats_message)
            logger.info(f"Пинг-сообщение отправлено пользователю {user.tg_user_id}")

        except Exception as e:
            logger.error(f"Ошибка при отправке пинг-сообщения: {str(e)}")
            # TODO: Возможно добавить повторные попытки отправки или логику алертинга

    async def get_research_current_status(self, research_id: int) -> str:
        research_status = await self.repo.status_repo.research_status.get_research_status(research_id=research_id)
        return research_status.status_name.value

    async def count_unresponded_assistant_message(self, telegram_id: int) -> int:
        """Получение всех неотвеченных сообщений от ассистента."""
        unresponded_messages = await self.repo.message_repo.assistant.fetch_assistant_messages_after_user(
            telegram_id=telegram_id)
        return len(unresponded_messages)

    async def calculate_send_time(self, telegram_id: int, time_delay: int) -> datetime:
        """Расчёт времени отправки следующего пинга."""
        last_user_message = await self.repo.message_repo.user.get_last_user_message_by_user_telegram_id(telegram_id)

        last_message_time = last_user_message.created_at.replace(
            tzinfo=timezone.utc) if last_user_message.created_at.tzinfo is None else last_user_message.created_at
        return last_message_time + timedelta(hours=time_delay)

    async def get_active_users(self, research_id) -> List[UserDTOFull]:
        """Получение пользователей со статусом IN_PROGRESS."""
        return await self.repo.status_repo.user_status.get_users_by_research_with_status(research_id=research_id,
                                                                                         status=UserStatusEnum.IN_PROGRESS)

    @staticmethod
    def generate_assistant_message_object(message: str, user: UserDTOFull,
                                          research_info: ResearchDTOFull) -> AssistantMessageDTOPost:
        """Генерация объекта сообщения ассистента."""
        return AssistantMessageDTOPost(
            text=message,
            chat_id=user.tg_user_id,
            to_user_id=user.tg_user_id,
            assistant_id=research_info.assistant_id,
            telegram_client_id=research_info.telegram_client_id
        )

    def generate_nats_message_object(self, message: str, user: UserDTOFull,
                                     research_info: ResearchDTOFull) -> NatsQueueMessageDTOStreem:
        """Генерация сообщения для публикации в очередь NATS."""
        headers = self.form_headers(
            {"telegram_client_name": research_info.telegram_client_id, "tg_user_id": user.tg_user_id})
        return NatsQueueMessageDTOStreem(
            message=message,
            subject=self.config.nats_subject,
            stream=self.config.nast_stream,
            headers=headers,
        )

    @staticmethod
    def form_headers(data: Dict[str, Any]) -> NatsTelegramHeaders:
        """Формирование заголовков для сообщения в NATS."""
        return NatsTelegramHeaders(
            telegram_client_name=str(data.get('telegram_client_name')),
            tg_user_id=str(data.get('tg_user_id'))
        )


class ResearchProcess:
    def __init__(self,
                 repository: RepoStorage,
                 communicator,
                 notifier,
                 publisher):

        self.repository = repository
        self.communicator = communicator
        self.notifier = notifier
        self.publisher = publisher
        self.research_starter = ResearchStarter(repository, communicator)
        self.research_stopper = ResearchStopper(repository, notifier)
        self.research_over_checker = ResearchOverChecker(repository, self.research_stopper)
        self.research_user_pingator = UserPingator(repo=self.repository, communicator=self.communicator, publisher=self.publisher)

    async def run(self, research_id: int) -> None:
        """ Основной цикл проведения исследования. """
        await self.research_starter.start_up_research(research_id)

        # Запуск асинхронных задач для проверки завершения исследования
        tasks = [
            self.research_over_checker.monitor_completion(research_id),
            self.research_user_pingator.ping_users(research_id)
        ]

        try:
            # Ждём, когда одна из задач завершится, остальные будут отменены
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            # Отмена всех оставшихся задач (например, пингатор может продолжать дольше нужного)
            for task in pending:
                task.cancel()

            logger.info(f'Все задачи исследования {research_id} завершены.')
        except Exception as e:
            # Обработка ошибок на глобальном уровне
            logger.error(f"Ошибка в процессе исследования {research_id}: {str(e)}")
            raise e


if __name__ == '__main__':
    async def main():
        # Создание необходимых объектов
        repository = RepoStorage()  # Пример: заменить на реальный экземпляр RepoStorage
        communicator = NatsBroker()  # Пример: заменить на реальный экземпляр NatsBroker или другого брокера
        notifier = TelegramNotificator()  # Пример: заменить на реальный экземпляр NatsBroker или другого брокера
        publisher = NatsPublisher()
        process = ResearchProcess(repository, communicator, notifier)

        # Укажите реальный идентификатор исследования
        research_id = 1  # Пример идентификатора исследования

        await process.run(research_id)


    asyncio.run(main())

#
# class ResearchStarter:
#
#     def __init__(self, repository: RepoStorage,
#                  communicator):
#         self.repository = repository
#         self.communicator = communicator
#
#     async def start_up_research(self, research_id: int) -> None:
#         """
#         Задача начать исследование, разослав сообщения пользователям
#
#         :param research_id:
#         :param client_id:
#         :return:
#         """
#
#         # Поставить статус исследования 1 (в работе)
#         await self.repository.status_repo.research_status.change_research_status(
#             research_id=research_id,
#             status=ResearchStatusEnum.IN_PROGRESS
#         )
#
#         user_group: List[UserDTOFull] = await self._get_user_in_research(research_id=research_id)
#         # Перевести всех пользователей в статус "в работе"
#
#         await self.repository.status_repo.user_status.change_status_group_of_user(
#             user_group=user_group,
#             status=UserStatusEnum.IN_PROGRESS
#         )
#         # Отправить приветственное сообщение всем пользователям
#
#         # TODO ответсвенного за отправку сообщения сделай ресерсера
#         await self.communicator.send_first_message(resarch_id=research_id)
#         logger.info("Все приветсвенныые сообщение отправил в запуске")
#         return
#
#     async def _get_user_in_research(self, research_id) -> List[UserDTOFull]:
#         users_in_research = await self.repository.user_in_research_repo.short.get_users_by_research_id(
#             research_id=research_id
#         )
#         return [user.tg_user_id for user in users_in_research]
#
#
# class ResearchStopper:
#
#     def __init__(self,
#                  repository: RepoStorage,
#                  notifier):
#
#         self.repository = repository
#         #TODO Написать нотифаер
#         self.notifier = notifier
#
#     async def complete_research(self, research_id) -> None:
#         """
#         Функция останавливает исследование, переводя его статус в необходимый, если выполняется какое-то из условий.
#         """
#
#         # Получение всех пользователей, участвующих в исследовании
#         user_group = await self._get_user_in_research(research_id=research_id)
#
#         logger.info('Начал завершение иследования  ____________________________ ...')
#         # Обновление статуса исследования в базе данных на "DONE"
#         await self.repository.status_repo.research_status.change_research_status(
#             research_id=research_id,
#             status=ResearchStatusEnum.DONE
#         )
#
#         # Обновление статуса всех пользователей, участвующих в исследовании на "DONE"
#         await self.repository.status_repo.user_status.change_status_group_of_user(
#             user_group=user_group,
#             status=UserStatusEnum.DONE
#         )
#
#         research_status = await self.repository.status_repo.research_status.get_research_status(
#             research_id=research_id)
#         user_in_progress = await self._get_users_in_progress(research_id=research_id)
#
#         # Проверка статуса исследования на "DONE" и что никто из пользователей не находится в процессе
#
#         if research_status.status_name != ResearchStatusEnum.IN_PROGRESS and not user_in_progress:
#             logger.info("Исследование завершено")
#             # TODO: отправить в шину данных сообщение, что исследование завершено (отправка в сервис уведомлений)
#             await self.notifier.notify_completion()
#         else:
#             logger.info("Исследование не завершено")
#             logger.info(f"Статус исследования: {research_status.status_name}")
#             logger.info(f"Пользователи в процессе: {user_in_progress}")
#
#             # TODO: обработать случаи, когда исследование не завершено, и причины, почему оно не завершено
#             await self.notifier.handle_incomplete_research()
#
#     async def _get_user_in_research(self, research_id) -> List[UserDTOFull]:
#         users_in_research = await self.repository.user_in_research_repo.short.get_users_by_research_id(
#             research_id=research_id
#         )
#         return [user.tg_user_id for user in users_in_research]
#
#     async def _get_users_in_progress(self, research_id):
#         return await self.repository.status_repo.user_status.get_users_by_research_with_status(
#             research_id=research_id,
#             status=UserStatusEnum.IN_PROGRESS)
#
#     # async def run_research(self):
#     #     event = asyncio.Event()
#     #     logger.info("Иследование запустилось в run ")
#     #     # запустить отслеживание сигналов завершения
#     #     # ping_task = self.user_manager.ping_users()
#     #
#     #     # Основная логика
#     #     await self.create_research()
#     #     await self.start_up_research()
#     #
#     #     is_research_time_over_task = self._is_research_time_over(event)
#     #     is_users_over_task = self._is_users_over(event)
#     #     # is_status_done = self._is_status_done(event)
#     #     stop_task = self.complete_research(event)
#     #
#     #     await asyncio.gather(
#     #         # is_status_done,
#     #         is_research_time_over_task,
#     #         is_users_over_task,
#     #         stop_task
#     #     )
#
#
# class ResearchTimeOver:
#     def __init__(self, repository, stopper):
#         self.repository = repository
#         self.stopper = stopper
#         self.settings = self._load_settings()
#
#     @staticmethod
#     def _load_settings() -> Dict[str, int]:
#         return {
#             "delay_is_research_time_over": 60,
#         }
#
#     async def is_research_time_over(self, research_id) -> None:
#         """ Проверяет, завершено ли время исследования. """
#         end_date = await self._get_research_end_date(research_id)
#
#         if not end_date:
#             logger.info(f"Нету конечной даты {research_id}")
#             return
#
#         while True:
#
#             research_status = await self.get_research_current_status(research_id=research_id)
#
#             if datetime.now() >= end_date:
#                 await self.stopper.complete_research(research_id)
#                 logger.info(f"Завершил исследование по истечению времени {research_id}")
#                 break
#
#             if research_status not in [ResearchStatusEnum.IN_PROGRESS, ResearchStatusEnum.WAIT]:
#                 await self.stopper.complete_research(research_id)
#                 logger.info(f"Завершил исследование по смене статуса {research_id}")
#                 break
#
#             await asyncio.sleep(self.settings.get('delay_is_research_time_over', 60))
#
#     async def _get_research_end_date(self, research_id) -> datetime:
#         research = await self.repository.research_repo.short.get_research_by_id(research_id=research_id)
#
#         if research.end_date.tzinfo is not None:
#             # Если временная зона указана — убираем привязку к временной зоне
#             return research.end_date.replace(tzinfo=None)
#         else:
#             return research.end_date
#
#     async def get_research_current_status(self, research_id) -> str:
#         research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
#         return research_status.status_name.value
#
#
# class ResearchUserOver:
#
#     def __init__(self, repository, stopper):
#         self.repository = repository
#         self.stopper = stopper
#         self.settings = self._load_settings()
#
#     @staticmethod
#     def _load_settings() -> Dict[str, int]:
#         return {
#             "delay_is_users_over": 60,
#         }
#
#     async def is_users_over(self, research_id) -> None:
#
#         user_in_progress = await self._get_users_in_progress(research_id)
#
#         while True:
#
#             research_status = await self._get_research_current_status(research_id=research_id)
#
#             if not user_in_progress:
#                 await self.stopper.complete_research(research_id)
#                 logger.info(f"Завершил исследование, так как закончились пользователи {research_id}")
#                 break
#
#             if research_status not in [ResearchStatusEnum.IN_PROGRESS, ResearchStatusEnum.WAIT]:
#                 await self.stopper.complete_research(research_id)
#                 logger.info(f"Завершил исследование по смене статуса {research_id}")
#                 break
#
#             logger.info(f"Проверяю пользователей в прогрессе, их вот столько: {len(user_in_progress)}")
#             await asyncio.sleep(self.settings['delay_is_users_over'])
#             user_in_progress = await self._get_users_in_progress(research_id)
#
#     async def _get_users_in_progress(self, research_id):
#         return await self.repository.status_repo.user_status.get_users_by_research_with_status(
#             research_id=research_id,
#             status=UserStatusEnum.IN_PROGRESS)
#
#     async def _get_research_current_status(self, research_id) -> str:
#         research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
#         return research_status.status_name.value
