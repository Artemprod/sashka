import datetime

from typing import Any, List, Optional

from loguru import logger

from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.owner import ResearchOwnerDTO, ResearchOwnerFullDTO
from src.schemas.service.research import ResearchDTOPost, ResearchDTOFull, ResearchDTORel, ResearchDTOBeDb
from src.schemas.service.user import UserDTOFull, UserDTOBase, UserDTO
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.research.base import BaseResearchManager

from src.database.postgres.models.enum_types import UserStatusEnum, ResearchStatusEnum

from src.database.repository.storage import RepoStorage




# TODO переделать класс вынести в отдельные классы сущности ресерч создатель иследования и тд разные стратегии
class TelegramResearchManager(BaseResearchManager):
    def __init__(self,
                 repository: RepoStorage,
                 information_collector: TelegramUserInformationCollector):
        self._database_repository = repository
        self._information_collector = information_collector
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings():
        # TODO: Загрузить или установить настройки
        return {
            "delay_is_research_time_over": 60,
            "delay_is_users_over": 10
        }

    # TODO оптимизировать метод
    # TODO Вытащить создание овнера наружу из класса
    async def create_research(self, research: ResearchDTOPost, owner: ResearchOwnerDTO, ) -> ResearchDTORel:
        """Создает исследование в базе данных и назначает необходимые данные."""
        try:
            # TODO Испарвить овнера понять че хотел сервис айди 
            # Создаем овнера в базще еси нет
            print()
            owner = await self._create_new_owner(owner_dto=owner)
            telegram_client: TelegramClientDTOGet = await self._get_telegram_client()

            # Создать и сохранить исследование
            research_dto: ResearchDTOBeDb = self._create_research_dto(research, owner, telegram_client)
            db_research: ResearchDTOFull = await self._save_new_research(research_dto)

            # Ставим статус для исследования
            await self._set_research_status(db_research)

            users = [UserDTOBase(name=names) for names in research.examinees_user_names]
            # Собрать информацию о пользователях и добавить их в исследованиAе при первом контакте использовать только имя
            users_dto = await self._collect_user_information(telegram_client=telegram_client,
                                                             users=users)

            await self._add_users_to_research(users_dto)

            # Ставим статусы для пользователей
            await self._set_user_status(research=research)

            # Связать пользователей с исследованием
            await self._bind_users_to_research(db_research)

            # Возврат DTO с сохраненным исследованием
            saved_research: ResearchDTORel = await self._get_saved_research(db_research.research_id)
            return saved_research

        except Exception as e:
            logger.error(f"Error during research creation: {e} \n {e.args}")
            raise

    async def get_research_info(self, research: ResearchDTOPost):
        full_info = await self._database_repository.research_repo.full.get_research_by_id(
            research_id=research.research_id)
        logger.info(f"Вот полная инфа {full_info}")
        return full_info

    async def _set_research_status(self, db_research: ResearchDTOFull):
        await self._database_repository.status_repo.research_status.add_research_status(
            values={
                "research_id": db_research.research_id,
                "status_name": ResearchStatusEnum.WAIT,
                "created_at": datetime.datetime.now()
            }
        )

    async def _set_user_status(self, research: ResearchDTOPost) -> None:
        """ Устанавливает статус пользователей и возвращает список пользователей, для которых статус не был установлен. """
        db_users = []
        for user in research.examinees_ids:
            get_users_db_id = await self._database_repository.user_in_research_repo.short.get_user_id_by_telegram_id(
                telegram_id=user)
            db_users.append(get_users_db_id)

        for user_id in db_users:
            try:
                print()
                await self._database_repository.status_repo.user_status.add_user_status(
                    values={
                        "user_id": user_id,
                        "status_name": UserStatusEnum.WAIT,
                        "created_at": datetime.datetime.now()
                    }
                )
            except Exception as e:
                logger.error(e)

    # Asynchronous helper methods for database operations

    async def _create_new_owner(self, owner_dto: ResearchOwnerDTO) -> ResearchOwnerFullDTO:
        owner = await self._database_repository.owner_repo().short.get_owner_by_service_id(
            service_id=owner_dto.service_owner_id)

        # TODO Сделать нормальную авторизациб и аутентификацию для того тчобы создовать иследования
        # ЕЩПроблема с созданием овнера получение его сервиса
        if not owner:
            owner = await self._database_repository.owner_repo().short.add_owner(values=owner_dto.dict())
        return owner

    #TODO Выдвать клиента только в случае если нет данных от пользователя какого клиента выдовать
    async def _get_telegram_client(self) -> TelegramClientDTOGet:
        clients = [client for client in await self._database_repository.client_repo.get_all() if client.session_string]
        return clients[-1] if clients else None

    async def _collect_user_information(self, telegram_client: TelegramClientDTOGet,
                                        users: List[UserDTOBase]) -> Optional[
        List[UserDTO]]:

        try:
            users_info = await self._information_collector.collect_users_information(
                users=users,
                client=telegram_client
            )
            return users_info
        except Exception as e:
            raise e

    def _create_research_dto(self, research: ResearchDTOPost, owner: Any, telegram_client: Any) -> ResearchDTOBeDb:
        return ResearchDTOBeDb(

            owner_id=owner.owner_id,
            telegram_client_id=telegram_client.telegram_client_id,
            **research.dict()
        )

    async def _save_new_research(self, research_dto: ResearchDTOBeDb) -> ResearchDTOFull:
        return await self._database_repository.research_repo.short.save_new_research(
            values=research_dto.dict(exclude={'examinees_ids', 'examinees_user_names'})
        )

    async def _get_saved_research(self, research_id: int) -> ResearchDTORel:
        return await self._database_repository.research_repo.full.get_research_by_id(research_id=research_id)

    async def _add_users_to_research(self, users_dto: List[UserDTO]) -> Optional[List[UserDTOFull]]:
        return await self._database_repository.user_in_research_repo.short.add_many_users(
            values=[user.dict() for user in users_dto]
        )

    async def _bind_users_to_research(self, research: ResearchDTOFull) -> None:
        db_users = []
        for user in research.examinees_ids:
            get_users_db_id = await self._database_repository.user_in_research_repo.short.get_user_by_telegram_id(
                telegram_id=user)
            db_users.append(get_users_db_id)

        for db_user in db_users:
            await self._database_repository.user_in_research_repo.short.bind_research(
                user_id=db_user.user_id,
                research_id=research.research_id
            )
