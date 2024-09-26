import asyncio
import datetime
from datetime import date
from typing import Any, List

from datasourse_for_test.resercch_imirtation import UserResearch
from src_v0.database.connections.redis_connect import RedisCash
from src_v0.database.postgres.engine.session import DatabaseSessionManager
from src_v0.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src_v0.database.postgres.models.research import Research
from src_v0.database.postgres.models.user import User
from src_v0.database.repository.storage import RepoStorage
from src_v0.resrcher.models import ResearchCashDTO
from src_v0.resrcher.open_ai_namager import OpenAiresponser
from src_v0.resrcher.user_cimmunication import Communicator
from src_v0.resrcher.user_manager import UserManager
from src_v0.database.database_t import comon_database as reserch_database
from src_v0.schemas.research import ResearchDTO, ResearchOwnerDTO
from src_v0.schemas.user import UserDTO


class BaseResearcher:
    ...


# TODO Переделать входящие данные это должен быть DTO Research
# TODO В настройках передовать атрибуты для инициализхации композиуия

# Я думаю это фасад для управнеия иследованием ( собирает логику несколких классов )
class TelegramResearcher(BaseResearcher):
    def __init__(self, research: UserResearch, repository: RepoStorage):
        self.database_repository = repository
        self.research = research
        # TODO для теста сделаю словарь потом заменгить на дто тут данные обновляються
        self.research_data = None
        self.user_manager = UserManager(repo=repository)
        storage = RepoStorage(database_session_manager=DatabaseSessionManager(
            database_url='postgresql+asyncpg://postgres:1234@localhost:5432/cusdever_client'))
        self.communicator = Communicator(repo=storage, ai_responser=OpenAiresponser(repo=storage))

        # TODO Заменить инициализации вынести в инит как аргументы либо в настройках указать все атрибуты для инициализации классов

        #TODO инициализироваать настроки откуда то
        self.settings = {
            "delay_is_research_time_over": 60,
            "delay_is_users_over": 10
        }

    #TODO оптимизировать метод
    async def create_research(self):
        """Создает исследование в базе данных и назначает необходимые данные."""
        try:
            owner = await self._get_or_create_owner(self.research.owner.service_owner_id)
            telegram_client = await self._get_telegram_client()

            # Создать и сохранить исследование
            research_dto = self._create_research_dto(owner, telegram_client)
            db_research = await self._save_new_research(research_dto)

            await self.database_repository.status_repo.research_status.add_research_status(
                values={"research_id": db_research.research_id, "status_name": ResearchStatusEnum.WAIT,
                        "created_at": datetime.datetime.now()}
            )

            # Собрать информацию о пользователях и добавить их в исследование
            users_dto = await self._collect_users_information(self.research.user_ids)
            db_users = await self._add_users_to_research(users_dto=users_dto)

            for user_id in [user.user_id for user in db_users]:
                await self.database_repository.status_repo.user_status.add_user_status(
                    values={"user_id": user_id, "status_name": UserStatusEnum.WAIT,
                            "created_at": datetime.datetime.now()}
                )

            # Связать пользователей с исследованием
            await self._bind_users_to_research(db_users, db_research.research_id)

            # Возврат DTO с сохраненным исследованием
            saved_research = await self._get_saved_research(db_research.research_id)
            self.research_data = saved_research
            return saved_research

        except Exception as e:
            # Логирование ошибок (добавить соответствующий логгер)
            print(f"Error during research creation: {e}")
            raise

    async def _get_assistant(self, assistant_id: int) -> Any:
        return await self.database_repository.assistant_repo.get_assistant(assistant_id=assistant_id)

    async def _get_or_create_owner(self, service_owner_id: int) -> Any:
        owner = await self.database_repository.owner_repo().short.get_owner_by_service_id(service_id=service_owner_id)
        if not owner:
            owner_dto = ResearchOwnerDTO(**self.research.owner.to_dict())
            owner = await self.database_repository.owner_repo().short.add_owner(values=owner_dto.dict())
        return owner

    async def _get_telegram_client(self) -> Any:
        return await self.database_repository.client_repo.get_client_by_id(client_id=1)

    def _create_research_dto(self, owner: Any, telegram_client: Any) -> ResearchDTO:
        return ResearchDTO(
            owner_id=owner.owner_id,
            telegram_client_id=telegram_client.telegram_client_id,
            **self.research.to_dict()
        )

    async def _save_new_research(self, research_dto: ResearchDTO) -> Any:
        return await self.database_repository.research_repo.short.save_new_research(values=research_dto.dict())

    async def _get_saved_research(self, research_id: int) -> Research:
        return await self.database_repository.research_repo.full.get_research_by_id(research_id=research_id)

    async def _collect_users_information(self, user_telegram_ids: List[int]) -> List[UserDTO]:
        return await self.user_manager.collect_users_information(user_telegram_ids=user_telegram_ids)

    async def _add_users_to_research(self, users_dto: List) -> List[Any]:
        return await self.database_repository.user_in_research_repo.short.add_many_users(
            values=[user.dict() for user in users_dto])

    async def _bind_users_to_research(self, db_users: List[Any], research_id: int) -> None:
        for db_user in db_users:
            await self.database_repository.user_in_research_repo.short.bind_research(
                user_id=db_user.user_id, research_id=research_id
            )


    async def _is_research_time_over(self, event: asyncio.Event) -> None:
        """
        Проверяет, завершено ли время исследования.
        :param event: asyncio.Event для завершения проверки времени исследования.
        """
        while not event.is_set():
            minutes_left = await self._count_time_difference_in_minutes()
            print("Минут осталось ", minutes_left)
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
        if self.research_data is not None:
            current_time = datetime.datetime.now()
            time_difference = self.research_data.end_date - current_time
            minutes_left = int(time_difference.total_seconds() / 60)
            return minutes_left

    async def _is_users_over(self, event: asyncio.Event) -> None:
        user_in_progress = await self._get_users_in_progress()
        if not user_in_progress:
            print('Нет пользователей в исследовании')
            event.set()
            return

        while not event.is_set():
            if not user_in_progress:
                event.set()
                print(f"Завершил исследование, так как закончились пользователи {self.research_data.theme}")
                break

            print(f"Проверяю пользователей в прогрессе, их вот столько: {len(user_in_progress)}")
            await asyncio.sleep(self.settings['delay_is_users_over'])
            user_in_progress = await self._get_users_in_progress()

    async def _get_users_in_progress(self):
        return await self.database_repository.status_repo.user_status.get_users_by_research_with_status(
            research_id=self.research_data.research_id,
            status=UserStatusEnum.IN_PROGRESS)


    async def start_up_research(self) -> None:
        """
        Задача начать исследование, разослав сообщения пользователям

        :param research_id:
        :param client_id:
        :return:
        """
        # TODO сделай проверку на то все ли данные есть каких данных нет дособрать
        # Поставить статус исследования 1 (в работе)
        await self.database_repository.status_repo.research_status.change_research_status(
            research_id=self.research_data.research_id,
            status=ResearchStatusEnum.IN_PROGRESS
        )
        user_group = await self._get_user_in_research()
        # Перевести всех пользователей в статус "в работе"
        await self.database_repository.status_repo.user_status.change_status_group_of_user(
            user_group=user_group,
            status=UserStatusEnum.IN_PROGRESS
        )
        # Отправить приветственное сообщение всем пользователям
        #TODO ответсвенного за отправку сообщения сделай ресерсера
        await self.communicator.send_first_message(resarch_id=self.research_data.research_id)
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
        print('Начал завершение иследования  ____________________________ ...')
        # Обновление статуса исследования в базе данных на "DONE"
        await self.database_repository.status_repo.research_status.change_research_status(
            research_id=self.research_data.research_id,
            status=ResearchStatusEnum.DONE
        )

        # Обновление статуса всех пользователей, участвующих в исследовании на "DONE"
        await self.database_repository.status_repo.user_status.change_status_group_of_user(
            user_group=user_group,
            status=UserStatusEnum.DONE
        )

        research_status = await self.database_repository.status_repo.research_status.get_research_status(
            research_id=self.research_data.research_id)
        user_in_progress = await self._get_users_in_progress()
        # Проверка статуса исследования на "DONE" и что никто из пользователей не находится в процессе

        if research_status.status_name != ResearchStatusEnum.IN_PROGRESS and not user_in_progress:
            print("Исследование завершено")
            # TODO: отправить в шину данных сообщение, что исследование завершено (отправка в сервис уведомлений)
            # await self.notify_completion()
        else:
            print("Исследование не завершено")
            print(f"Статус исследования: {research_status.status_name}")
            print(f"Пользователи в процессе: {user_in_progress}")

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

        # Основная логика
        await self.create_research()
        await self.start_up_research()

        is_research_time_over_task = self._is_research_time_over(event)
        is_users_over_task = self._is_users_over(event)
        # is_status_done = self._is_status_done(event)
        stop_task = self.complete_research(event)

        await asyncio.gather(
            # is_status_done,
            is_research_time_over_task,
            is_users_over_task,
            stop_task
        )

    async def abort_research(self):
        await self.database_repository.status_repo.research_status.change_research_status(
            research_id=self.research_data.research_id,
            status=ResearchStatusEnum.ABORTED
        )
        print("ABBORTED RESEARCH")

    async def pause_research(self):
        await self.database_repository.status_repo.research_status.change_research_status(
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

    # async def _start_cashing(self, event: asyncio.Event) -> None:
    #     """
    #     Обновляет данные в классе из базы.
    #     Зависит от события.
    #
    #     1. Проверяет, есть ли данные в Redis.
    #     2. Если нет, обновляет данные из базы данных.
    #     3. Возвращает данные.
    #
    #     :param event: asyncio.Event для завершения обновления данных.
    #     """
    #     while not self.research_data.research_id:
    #         await asyncio.sleep(1)
    #     # Спросим первый раз, есть ли данные в кэше
    #     research_data = await self.data_cash.get_research_data(research=self.research_data.research_id)
    #
    #     if not research_data:
    #         # Если данных нет, асинхронно обновляем данные из базы и записываем их в кэш
    #         await self._update_cash()
    #
    #     # Пока событие не установлено, обновляем данные в заданном интервале
    #     refresh_interval = 5  # Вынесите в настройки, например, self.config.cache_refresh_interval
    #
    #     while not event.is_set():
    #         await self._update_cash()
    #         await self._get_cash()
    #         print("Кэш данные обновлены ", self.research_data)
    #         await asyncio.sleep(refresh_interval)
    #     else:
    #         print("Обновление данных по заврегшению")
    #         await self._update_cash()
    #         await self._get_cash()
    #
    # async def _update_cash(self) -> None:
    #     """
    #     Обновляет кэш данными из базы данных.
    #     """
    #     research_data_from_db: ResearchCashDTO = await self.database_repository.research_cash_repo.get_cash_information(
    #         research_id=self.research_data.research_id
    #     )
    #     # Асинхронное обновление данных в Redis
    #     await self.data_cash.update_data_in_cash(research=self.research_data.research_id,
    #                                              data=research_data_from_db.dict())
    #     self.research_data = ResearchCashDTO(**research_data_from_db.dict())
    #
    # async def _get_cash(self) -> None:
    #     """
    #     Получает данные из кэша и обновляет атрибуты класса.
    #     """
    #     cashing_data = await self.data_cash.get_research_data(research=self.research_data.research_id)
    #     # Обновляем атрибуты экземпляра класса на основе данных из кэша
    #     self.research_data = ResearchCashDTO(**cashing_data)

