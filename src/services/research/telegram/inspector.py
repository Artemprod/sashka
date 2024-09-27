import asyncio
import math
from datetime import datetime
from typing import List, Dict

from faststream.nats import NatsBroker
from loguru import logger

from src.schemas.user import UserDTOFull
from src.services.publisher.notification import TelegramNotificator

from src_v0.database.postgres.models.enum_types import ResearchStatusEnum, UserStatusEnum
from src_v0.database.repository.storage import RepoStorage
from src_v0.resrcher.open_ai_namager import OpenAiresponser


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


class ResearchTimeOver:
    def __init__(self, repository, stopper):
        self.repository = repository
        self.stopper = stopper
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, int]:
        return {"delay_is_research_time_over": 60}

    async def is_research_time_over(self, research_id) -> None:
        end_date = await self._get_research_end_date(research_id)
        if not end_date:
            logger.info(f"Нету конечной даты {research_id}")
            return
        while True:
            research_status = await self.get_research_current_status(research_id=research_id)
            if datetime.now() >= end_date:
                await self.stopper.complete_research(research_id)
                logger.info(f"Завершил исследование по истечению времени {research_id}")
                break
            if research_status not in [ResearchStatusEnum.IN_PROGRESS, ResearchStatusEnum.WAIT]:
                await self.stopper.complete_research(research_id)
                logger.info(f"Завершил исследование по смене статуса {research_id}")
                break
            await asyncio.sleep(self.settings.get('delay_is_research_time_over', 60))

    async def _get_research_end_date(self, research_id) -> datetime:
        research = await self.repository.research_repo.short.get_research_by_id(research_id=research_id)
        if research.end_date.tzinfo is not None:
            return research.end_date.replace(tzinfo=None)
        else:
            return research.end_date

    async def get_research_current_status(self, research_id) -> str:
        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        return research_status.status_name.value


class ResearchUserOver:
    def __init__(self, repository, stopper):
        self.repository = repository
        self.stopper = stopper
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, int]:
        return {"delay_is_users_over": 60}

    async def is_users_over(self, research_id) -> None:
        user_in_progress = await self._get_users_in_progress(research_id)
        while True:
            research_status = await self._get_research_current_status(research_id=research_id)
            if not user_in_progress:
                await self.stopper.complete_research(research_id)
                logger.info(f"Завершил исследование, так как закончились пользователи {research_id}")
                break
            if research_status not in [ResearchStatusEnum.IN_PROGRESS, ResearchStatusEnum.WAIT]:
                await self.stopper.complete_research(research_id)
                logger.info(f"Завершил исследование по смене статуса {research_id}")
                break
            logger.info(f"Проверяю пользователей в прогрессе, их вот столько: {len(user_in_progress)}")
            await asyncio.sleep(self.settings['delay_is_users_over'])
            user_in_progress = await self._get_users_in_progress(research_id)

    async def _get_users_in_progress(self, research_id):
        return await self.repository.status_repo.user_status.get_users_by_research_with_status(
            research_id=research_id, status=UserStatusEnum.IN_PROGRESS
        )

    async def _get_research_current_status(self, research_id) -> str:
        research_status = await self.repository.status_repo.research_status.get_research_status(research_id=research_id)
        return research_status.status_name.value


class Pingator:
    max_pings = 4
    ping_attempts = 20

    def __init__(self,
                 repo: RepoStorage,
                 communicator: OpenAiresponser,
                 settings=None):

        self.settings = settings
        self.repo = repo
        self.communicator = communicator

    # TODO не забудб что тут User это модель ORM
    async def ping_users(self, research_id):
        """Пинг пользователей до тех пор, пока есть активные пользователи."""
        # TODO вощможно стоит подумать над тем как управлять циклам до каких пор делать пинг ?

        while True:
            users: List[UserDTOFull] = await self.get_active_users(research_id)

            if not users:  # Если нет активных пользователей, выходим из цикла
                logger.info("Все пользователи завершили задачи. Остановка пинга.")
                break

            # Обрабатываем пинг для всех пользователей одновременно
            await asyncio.gather(*[self.handle_user_ping(user) for user in users])
            await asyncio.sleep(1)  # Задержка перед следующим пингом

    async def get_active_users(self, research_id) -> List[UserDTOFull]:
        """Получение пользователей со статусом IN_PROGRESS."""
        return await self.repo.status_repo.user_status.get_users_by_research_with_status(
            research_id=research_id,
            status=UserStatusEnum.IN_PROGRESS
        )

    async def handle_user_ping(self, user: UserDTOFull):
        """Проверка времени последнего сообщения и выполнение пинга.
        если не 0 то дальше по логике
        """
        logger.info("_____________users", user.user_id)
        unresponed_messages = await self.count_unresponed_assistant_message(user.tg_user_id)
        logger.info("_____________unresponed_messages", unresponed_messages, "_______ user_id", user.user_id)
        if unresponed_messages == 0:
            return

        if unresponed_messages > UserManager.max_pings:
            logger.info(f"Превышено максимальное количество пингов для пользователя {user.tg_user_id}.")
            return

        time_delay = self.calculate_ping_delay(unresponed_messages)
        logger.info("_____________time_delay", time_delay, "_______ user_id", user.user_id)
        send_time = await self.calculate_send_data(telegram_id=user.tg_user_id, time_delay=time_delay)
        logger.info("______________Время когда должно быть отправдено сообщение", send_time, "_______ user_id",
                    user.user_id)
        # TODO решить вопрос с временными зонами (конверитровать серверное время или еще как то )
        current_time_utc = datetime.datetime.now(datetime.timezone.utc)
        # Если время отправки должно быть меньше или равно текущему времени в UTC
        if send_time <= current_time_utc:
            await self.send_ping_message(user=user, prompt_number=unresponed_messages)

    async def get_ping_prompt(self, number_of_message):
        message = await self.repo.ping_prompt_repo.get_ping_prompt_by_order_number(ping_order_number=number_of_message)
        return message

    async def count_unresponed_assistant_message(self, telegram_id) -> int:
        """Получение всех неотвеченых сообщений от ассистента."""
        unresponsed_assistant_messages = await self.repo.message_repo.assistant.fetch_assistant_messages_after_user(
            telegram_id=telegram_id)
        return len(unresponsed_assistant_messages)

    async def calculate_send_data(self, time_delay, telegram_id):
        # TODO сделайть управление локальной тайм зоной
        # Проблема в коныертации таймзоны в локальную на сервере время одно на компьютере другое

        last_user_message = await self.repo.message_repo.user.get_last_user_message_by_user_telegram_id(telegram_id)
        if last_user_message.created_at.tzinfo is None:
            # Если временная зона не указана — добавляем явную привязку к UTC
            last_message_time = last_user_message.created_at.replace(tzinfo=datetime.timezone.utc)
        else:
            last_message_time = last_user_message.created_at

            # Возвращаем время последнего сообщения с добавленной задержкой
        return last_message_time + datetime.timedelta(seconds=time_delay * 10)

    def calculate_ping_delay(self, n) -> int | None:
        """
        Функция для вычисления задержки пинга на основе входного значения n.

        Аргументы:
        n (int): Входное число, для которого нужно рассчитать задержку.

        Возвращает:
        float: Рассчитанное значение задержки пинга.
        """
        if n < 0:
            logger.info("Wrong input, n must be non-negative")
            return None  # Возвращаем None вместо пустого return
        elif n <= 3:
            # Используем math.factorial и math.sqrt для малых значений n
            return int(math.ceil(math.factorial(n + 1) - 1))
        else:
            # Логарифмическая функция для n > 3
            return int(math.ceil(10 * math.log(n) * (n - 3) + 24))

    async def send_ping_message(self, user, prompt_number):
        """Отправка пинг-сообщения."""
        #TODO
        prompt_object = await self.get_ping_prompt(number_of_message=prompt_number)

        message = await self.communicator.one_message(user_prompt=prompt_object.prompt,
                                                      system_prompt=prompt_object.system_prompt)

        assistan_message = {"text": message,
                            "chat_id": 1,
                            "to_user_id": user.tg_user_id,
                            "assistant_id": 1,
                            "telegram_client_id": 1}

        await self.repo.message_repo.assistant.save_new_message(values=assistan_message)


class ResearchProcess:
    def __init__(self, repository: RepoStorage, communicator, notifier):
        self.repository = repository
        self.communicator = communicator
        self.notifier = notifier
        self.research_starter = ResearchStarter(repository, communicator)
        self.research_stopper = ResearchStopper(repository, notifier)
        self.research_time_over = ResearchTimeOver(repository, self.research_stopper)
        self.research_user_over = ResearchUserOver(repository, self.research_stopper)

    async def run(self, research_id: int) -> None:
        await self.research_starter.start_up_research(research_id)

        done, pending = await asyncio.wait(
            [
                self.research_time_over.is_research_time_over(research_id),
                self.research_user_over.is_users_over(research_id)
            ],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        logger.info('Все задачи завершены')


if __name__ == '__main__':
    async def main():
        # Создание необходимых объектов
        repository = RepoStorage()  # Пример: заменить на реальный экземпляр RepoStorage
        communicator = NatsBroker()  # Пример: заменить на реальный экземпляр NatsBroker или другого брокера
        notifier = TelegramNotificator()  # Пример: заменить на реальный экземпляр NatsBroker или другого брокера
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
