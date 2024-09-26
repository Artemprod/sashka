import datetime
import random

from typing import Any, List, Optional

from datasourse_for_test.resercch_imirtation import UserResearch
from src.schemas.client import TelegramClientDTO
from src.schemas.owner import ResearchOwnerDTO
from src.schemas.research import ResearchDTO, ResearchDTOFull, ResearchDTORel
from src.schemas.user import UserDTOFull
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.research.base import BaseResearchManager

from src_v0.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum
from src_v0.database.postgres.models.research import Research

from src_v0.database.repository.storage import RepoStorage

from src_v0.schemas.user import UserDTO


# TODO Переделать входящие данные это должен быть DTO Research
# TODO В настройках передовать атрибуты для инициализхации композиуия

# Я думаю это фасад для управнеия иследованием ( собирает логику несколких классов )
class TelegramResearcheManager(BaseResearchManager):

    def __init__(self,
                 research: ResearchDTO,
                 repository: RepoStorage,
                 information_collector: TelegramUserInformationCollector):

        self._database_repository = repository
        self._research = research
        self._information_collector = information_collector

        # TODO инициализироваать настроки откуда то
        # self.settings = {
        #     "delay_is_research_time_over": 60,
        #     "delay_is_users_over": 10
        # }

    # TODO оптимизировать метод
    async def create_research(self) -> ResearchDTORel:
        """Создает исследование в базе данных и назначает необходимые данные."""

        try:
            owner: ResearchOwnerDTO = await self._get_or_create_owner(self._research.owner.service_owner_id)

            telegram_client: TelegramClientDTO = await self._get_telegram_client()

            # Создать и сохранить исследование
            research_dto: ResearchDTOFull = self._create_research_dto(owner, telegram_client)

            db_research: ResearchDTOFull = await self._save_new_research(research_dto)
            # Ставим статус для ислендования
            await self._set_research_status(db_research)

            # Собрать информацию о пользователях и добавить их в исследование
            users_dto: List[UserDTOFull] = await self._collect_user_information(telegram_client_name=telegram_client.name)

            users_in_database = await self._add_users_to_research(users_dto=users_dto)

            # Ставим статусы для пользовательей
            await self._set_user_status(users_in_database)

            # Связать пользователей с исследованием
            await self._bind_users_to_research(users_in_database, db_research.research_id)

            # Возврат DTO с сохраненным исследованием
            saved_research = await self._get_saved_research(db_research.research_id)

            self.research_data = saved_research
            return saved_research

        except Exception as e:
            # Логирование ошибок (добавить соответствующий логгер)
            print(f"Error during research creation: {e}")
            raise

    async def _set_research_status(self, db_research):
        await self._database_repository.status_repo.research_status.add_research_status(
            values={"research_id": db_research.research_id,
                    "status_name": ResearchStatusEnum.WAIT,
                    "created_at": datetime.datetime.now(datetime.timezone.utc)}
        )

    async def _set_user_status(self, db_users):
        for user_id in [user.user_id for user in db_users]:
            await self._database_repository.status_repo.user_status.add_user_status(
                values={"user_id": user_id,
                        "status_name": UserStatusEnum.WAIT,
                        "created_at": datetime.datetime.now(datetime.timezone.utc)}
            )

    async def _get_assistant(self, assistant_id: int) -> Any:
        return await self._database_repository.assistant_repo.get_assistant(assistant_id=assistant_id)

    async def _get_or_create_owner(self, service_owner_id: int) -> ResearchOwnerDTO:
        owner = await self._database_repository.owner_repo().short.get_owner_by_service_id(service_id=service_owner_id)
        if not owner:
            owner_dto = ResearchOwnerDTO(**self._research.owner.to_dict())
            owner = await self._database_repository.owner_repo().short.add_owner(values=owner_dto.dict())
        return owner

    async def _get_telegram_client(self) -> TelegramClientDTO:

        # TODO получение и привязка клиента к иследование
        # Получить того клиента который не в иследовании авторизован и работает
        # Добавить таблицу статусов и выдвать клиента колторый не занят и есть сессия и активен

        # Алгоритм поиска клиента по тсатусу активен 
        clients = [client for client in await self._database_repository.client_repo.get_all() if client.session_string]
        return clients[-1]

    async def _collect_user_information(self, telegram_client_name) -> Optional[List[UserDTOFull]]:
        async with self._information_collector as a:
            try:
                users = a.collect_users_information(user_telegram_ids=self._research.user_ids,
                                                    client_name=telegram_client_name)
                return users
            except Exception as e:
                raise e

    def _create_research_dto(self, owner: Any, telegram_client: Any) -> ResearchDTOFull:
        return ResearchDTOFull(
            owner_id=owner.owner_id,
            telegram_client_id=telegram_client.telegram_client_id,
            **self._research.to_dict()
        )

    async def _save_new_research(self, research_dto: ResearchDTO) -> ResearchDTOFull:
        return await self._database_repository.research_repo.short.save_new_research(values=research_dto.dict())

    async def _get_saved_research(self, research_id: int) -> Research:
        return await self._database_repository.research_repo.full.get_research_by_id(research_id=research_id)

    async def _add_users_to_research(self, users_dto: List) -> List[Any]:
        return await self._database_repository.user_in_research_repo.short.add_many_users(
            values=[user.dict() for user in users_dto])

    async def _bind_users_to_research(self, db_users: List[Any], research_id: int) -> None:
        for db_user in db_users:
            await self._database_repository.user_in_research_repo.short.bind_research(
                user_id=db_user.user_id, research_id=research_id
            )
