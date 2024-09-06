import asyncio
import datetime
from datetime import date
from typing import Any, List

from datasourse_for_test.resercch_imirtation import UserResearch
from src.database.connections.redis_connect import RedisCash
from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src.database.postgres.models.research import Research
from src.database.postgres.models.user import User
from src.database.repository.storage import RepoStorage
from src.resrcher.models import ResearchCashDTO
from src.resrcher.user_cimmunication import Communicator
from src.resrcher.user_manager import UserManager
from src.database.database_t import comon_database as reserch_database
from src.schemas.research import ResearchDTO, ResearchOwnerDTO
from src.schemas.user import UserDTO


class BaseResearcher:
    ...


# TODO Переделать входящие данные это должен быть DTO Research
# TODO В настройках передовать атрибуты для инициализхации композиуия

class TelegramResearcher(BaseResearcher):
    def __init__(self, research: UserResearch, repository: RepoStorage):
        self.database_repository = repository
        self.research = research
        # TODO для теста сделаю словарь потом заменгить на дто тут данные обновляються
        self.research_data = ResearchCashDTO()
        self.user_manager = UserManager()
        self.communicator = Communicator()
        # TODO Заменить инициализации вынести в инит как аргументы либо в настройках указать все атрибуты для инициализации классов

        self.data_cash = RedisCash()
        self.settings = {
            "delay_is_research_time_over": 60,
            "delay_is_users_over": 10
        }

    async def create_research(self):
        """Создает исследование в базе данных и назначает необходимые данные"""

        # TODO Обработка ошибок
        user_status = await self._get_user_status(UserStatusEnum.WAIT)
        research_status = await self._get_research_status(ResearchStatusEnum.WAIT)
        assistant = await self._get_assistant(self.research.assistant_id)
        owner = await self._get_or_create_owner(self.research.owner.service_owner_id)
        telegram_client = await self._get_telegram_client()

        # Создать и сохранить исследование
        research_dto = self._create_research_dto(owner, research_status, assistant, telegram_client)
        db_research = await self._save_new_research(research_dto)

        # Собрать информацию о пользователях и добавить их в исследование
        users_dto = await self._collect_users_information(self.research.user_ids)
        db_users = await self._add_users_to_research(users_dto, user_status)

        # Связать пользователей с исследованием
        await self._bind_users_to_research(db_users, db_research.research_id)
        # TODO Тут вернуть DTO класс с иследованием полным
        saved_research = await self._get_saved_research(db_research.research_id)
        self.research_data.research_id = saved_research.research_id
        return saved_research

    async def _get_user_status(self, status_name: UserStatusEnum) -> Any:
        return await self.database_repository.status_repo.user_status.get_status(status_name=status_name)

    async def _get_research_status(self, status_name: ResearchStatusEnum) -> Any:
        return await self.database_repository.status_repo.research_status.get_status(status_name=status_name)

    async def _get_assistant(self, assistant_id: int) -> Any:
        return await self.database_repository.assistant_repo.get_assistant(assistant_id=assistant_id)

    async def _get_or_create_owner(self, service_owner_id: int) -> Any:
        owner = await self.database_repository.owner_repo().short.get_owner_by_service_id(service_id=service_owner_id)
        if not owner:
            owner_dto = ResearchOwnerDTO(**self.research.owner.to_dict())
            owner = await self.database_repository.owner_repo().short.add_owner(values=owner_dto.dict())
        return owner

    # TODO выдвать клиента как то по другому например по стасту активен не активен пока для теста так
    async def _get_telegram_client(self) -> Any:
        return await self.database_repository.client_repo.get_client_by_id(client_id=1)

    # TODO Заменить на валидациб дто в класс приходит дто
    def _create_research_dto(self, owner: Any, research_status: Any, assistant: Any,
                             telegram_client: Any) -> ResearchDTO:
        return ResearchDTO(
            owner_id=owner.owner_id,
            research_status_id=research_status.status_id,
            # assistant_id=assistant.assistant_id,
            telegram_client_id=telegram_client.telegram_client_id,
            **self.research.to_dict()
        )

    async def _save_new_research(self, research_dto: ResearchDTO) -> Any:
        return await self.database_repository.research_repo.short.save_new_research(values=research_dto.dict())

    # TODO Не забывай что тут возвращаются объекты модели данных а не DTO допиши конвертацию
    async def _get_saved_research(self, research_id: int) -> Research:
        return await self.database_repository.research_repo.full.get_research_by_id(research_id=research_id)

    async def _collect_users_information(self, user_telegram_ids: List[int]) -> List[UserDTO]:
        return await self.user_manager.collect_users_information(user_telegram_ids=user_telegram_ids)

    # TODO Не забывай что тут возвращаются объекты модели данных а не DTO допиши конвертацию
    async def _add_users_to_research(self, users_dto: List[UserDTO], status: Any) -> List[Any]:
        return await self.database_repository.user_in_research_repo.short.add_many_users(
            [{"status_id": status.status_id, **user.dict()} for user in users_dto]
        )

    async def _bind_users_to_research(self, db_users: List[Any], research_id: int) -> None:
        for db_user in db_users:
            await self.database_repository.user_in_research_repo.short.bind_research(user_id=db_user.user_id,
                                                                                     research_id=research_id)

    async def _is_research_time_over(self, event: asyncio.Event) -> None:
        """
        Проверяет, завершено ли время исследования.
        :param event: asyncio.Event для завершения проверки времени исследования.
        """
        while not event.is_set():
            minutes_left = await self._count_time_difference_in_minutes()
            if minutes_left <= 0:
                event.set()
                print(f"Завершил исследование по истечению времени {self.research_data.theme}")
                break

            print(f"Проверяю оставшееся время: {minutes_left} минут")
            print(f"Статус исследования: {self.research_data.status}")
            await asyncio.sleep(self.settings.get('delay_is_research_time_over', 60))

    async def _count_time_difference_in_minutes(self) -> int:
        """
        Рассчитывает оставшееся время до окончания исследования в минутах.
        :return: Количество минут до окончания исследования.
        """
        current_time = datetime.datetime.now(datetime.timezone.utc)
        time_difference = self.research_data.end_date - current_time
        minutes_left = int(time_difference.total_seconds() / 60)
        return minutes_left

    async def _is_users_over(self, event: asyncio.Event) -> None:
        """
        Проверяет, есть ли пользователи, которые все еще участвуют в исследовании.
        :param event: asyncio.Event для завершения проверки наличия пользователей.
        """
        if self.research_data.user_in_progress == 0:
            print('Нет пользователей в исследовании')
            event.set()
            return

        while not event.is_set():
            if self.research_data.user_in_progress <= 0:
                # TODO: Обновить статусы всех пользователей в базе данных на 'done'
                event.set()
                print(f"Завершил исследование, так как закончились пользователи {self.research_data.theme}")
                break

            print(f"Проверяю пользователей в прогрессе, их вот столько: {self.research_data.user_in_progress}")
            await asyncio.sleep(self.settings.get('delay_is_users_over', 10))

    async def _is_status_done(self, event: asyncio.Event) -> None:
        """
        Проверяет статус исследования и завершает процесс, если статус изменился.
        :param event: asyncio.Event для завершения проверки статуса.
        """
        while not event.is_set():
            if self.research_data.research_status != ResearchStatusEnum.IN_PROGRESS:
                print(f"Завершил исследование по изменению статуса {self.research_data}")
                event.set()
                break

            await asyncio.sleep(self.settings.get('delay_is_users_over', 10))

    async def start_up_research(self) -> None:
        """
        Задача начать исследование, разослав сообщения пользователям

        :param research_id:
        :param client_id:
        :return:
        """
        # TODO сделай проверку на то все ли данные есть каких данных нет дособрать
        # Поставить статус исследования 1 (в работе)
        await self.database_repository.research_repo.short.change_research_status(
            research_id=self.research_data.research_id,
            status=ResearchStatusEnum.IN_PROGRESS
        )
        user_group = await self._get_user_in_research()
        # Перевести всех пользователей в статус "в работе"
        await self.database_repository.user_in_research_repo.short.change_status_group_of_user(
            user_group=user_group,
            status=UserStatusEnum.IN_PROGRESS
        )
        # Отправить приветственное сообщение всем пользователям
        await self.communicator.send_first_message(user_ids=user_group)
        print("Все приветсвенныые сообщение отправил в запуске")
        return

    async def complete_research(self, event: asyncio.Event) -> None:
        """
        Функция останавливает исследование, переводя его статус в необходимый, если выполняется какое-то из условий.
        """
        print('Жду сигнала к завершению ...')

        # Ждем сигнала для завершения
        await event.wait()

        # Получение всех пользователей, участвующих в исследовании
        user_group = await self._get_user_in_research()

        # Обновление статуса исследования в базе данных на "DONE"
        await self.database_repository.research_repo.short.change_research_status(
            research_id=self.research_data.research_id,
            status=ResearchStatusEnum.DONE
        )

        # Обновление статуса всех пользователей, участвующих в исследовании на "DONE"
        await self.database_repository.user_in_research_repo.short.change_status_group_of_user(
            user_group=user_group,
            status=UserStatusEnum.DONE
        )

        # Проверка статуса исследования на "DONE" и что никто из пользователей не находится в процессе
        if (self.research_data.research_status == ResearchStatusEnum.DONE and
                self.research_data.user_in_progress == 0):
            print("Исследование завершено")
            # TODO: отправить в шину данных сообщение, что исследование завершено (отправка в сервис уведомлений)
            # await self.notify_completion()
        else:
            print("Исследование не завершено")
            print(f"Статус исследования: {self.research_data.research_status}")
            print(f"Пользователи в процессе: {self.research_data.user_in_progress}")

            # TODO: обработать случаи, когда исследование не завершено, и причины, почему оно не завершено
            # await self.handle_incomplete_research()

    async def _get_user_in_research(self):
        users_in_research = await self.database_repository.user_in_research_repo.short.get_users_by_research_id(
            research_id=self.research_data.research_id
        )
        return [user.tg_user_id for user in users_in_research]

    async def run_research(self):
        event = asyncio.Event()
        print("Иследование запустилось в run ")
        # запустить отслеживание сигналов завершения
        # ping_task = self.user_manager.ping_users()
        cash_task = asyncio.create_task(self._start_cashing(event))
        try:
            # Основная логика
            await self.create_research()

            await self.start_up_research()

            is_research_time_over_task = self._is_research_time_over(event)
            is_users_over_task = self._is_users_over(event)
            is_status_done = self._is_status_done(event)
            stop_task = self.complete_research(event)

            await asyncio.gather(
                is_status_done,
                is_research_time_over_task,
                is_users_over_task,
                stop_task
            )

        finally:
            # Завершить задачу кэширования
            event.set()
            await cash_task
            print("Завершение задачи кэширования.")


    async def abort_research(self):
        await self.database_repository.research_repo.short.change_research_status(
            research_id=self.research_data.research_id,
            status=ResearchStatusEnum.ABORTED
        )
        print("ABBORTED RESEARCH")

    async def pause_research(self):
        await self.database_repository.research_repo.short.change_research_status(
            research_id=self.research_data.research_id,
            status=ResearchStatusEnum.PAUSE
        )
        print("PASUE RESEARCH")

    async def get_research_info(self, ):
        full_info = await self.database_repository.research_repo.full.get_research_by_id(
            research_id=self.research_data.research_id)
        print("Вот полная инфа")
        print(full_info)
        return full_info

    async def _start_cashing(self, event: asyncio.Event) -> None:
        """
        Обновляет данные в классе из базы.
        Зависит от события.

        1. Проверяет, есть ли данные в Redis.
        2. Если нет, обновляет данные из базы данных.
        3. Возвращает данные.

        :param event: asyncio.Event для завершения обновления данных.
        """
        while not self.research_data.research_id:
            await asyncio.sleep(1)
        # Спросим первый раз, есть ли данные в кэше
        research_data = await self.data_cash.get_research_data(research=self.research_data.research_id)

        if not research_data:
            # Если данных нет, асинхронно обновляем данные из базы и записываем их в кэш
            await self._update_cash()

        # Пока событие не установлено, обновляем данные в заданном интервале
        refresh_interval = 5  # Вынесите в настройки, например, self.config.cache_refresh_interval

        while not event.is_set():
            await self._update_cash()
            await self._get_cash()
            print("Кэш данные обновлены ", self.research_data)
            await asyncio.sleep(refresh_interval)
        else:
            print("Обновление данных по заврегшению")
            await self._update_cash()
            await self._get_cash()

    async def _update_cash(self) -> None:
        """
        Обновляет кэш данными из базы данных.
        """
        research_data_from_db: ResearchCashDTO = await self.database_repository.research_cash_repo.get_cash_information(
            research_id=self.research_data.research_id
        )
        # Асинхронное обновление данных в Redis
        await self.data_cash.update_data_in_cash(research=self.research_data.research_id,
                                                 data=research_data_from_db.dict())
        self.research_data = ResearchCashDTO(**research_data_from_db.dict())

    async def _get_cash(self) -> None:
        """
        Получает данные из кэша и обновляет атрибуты класса.
        """
        cashing_data = await self.data_cash.get_research_data(research=self.research_data.research_id)
        # Обновляем атрибуты экземпляра класса на основе данных из кэша
        self.research_data = ResearchCashDTO(**cashing_data)
