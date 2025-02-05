import datetime

from typing import Any, List, Optional, Union

from asyncpg import UniqueViolationError
from loguru import logger
from sqlalchemy.exc import IntegrityError

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
            owner = await self._create_new_owner(owner_dto=owner)
            telegram_client: TelegramClientDTOGet = await self._get_telegram_client()

            # Создать и сохранить исследование
            research_dto: ResearchDTOBeDb = self._create_research_dto(research, owner, telegram_client)
            db_research: ResearchDTOFull = await self._save_new_research(research_dto)

            # Ставим статус для исследования
            await self._set_research_status(db_research)

            await self._add_users_to_research(research, telegram_client=telegram_client)

            # Ставим статусы для пользователей
            await self._set_user_status(research=research)

            # Связать пользователей с исследованием
            await self._bind_users_to_research(research_id=db_research.research_id,
                                               research=research)

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
        """Устанавливает статус пользователей и возвращает список пользователей, для которых статус не был установлен."""
        db_users = set()

        # Получаем список user_id из базы данных для указанных telegram_id
        if research.examinees_ids:
            user_ids = await self._database_repository.user_in_research_repo.short.get_many_user_ids_by_telegram_ids(
                telegram_ids=research.examinees_ids
            )
            db_users.update(user_ids)

        # Получаем список user_id из базы данных для указанных имен пользователей
        if research.examinees_user_names:
            user_ids = await self._database_repository.user_in_research_repo.short.get_many_user_ids_by_usernames(
                usernames=research.examinees_user_names
            )
            db_users.update(user_ids)

        for user_id in db_users:
            if user_id is None:
                continue
            try:
                # Пытаемся добавить новый статус для пользователя
                await self._database_repository.status_repo.user_status.add_user_status(
                    values={
                        "user_id": user_id,
                        "status_name": UserStatusEnum.WAIT,
                        "created_at": datetime.datetime.now(),
                    }
                )
            except IntegrityError as e:
                # Проверяем, если это ошибка уникальности
                logger.info(f"Повторяющееся значение ключа для user_id={user_id}: {e}")
                # Обновляем статус пользователя, если запись уже существует
                await self._database_repository.status_repo.user_status.update_user_status(
                    user_id=user_id, status=UserStatusEnum.WAIT
                )
            except Exception as e:
                logger.error(f"Неизвестная ошибка для user_id={user_id}: {e}")

    # Asynchronous helper methods for database operations

    async def _create_new_owner(self, owner_dto: ResearchOwnerDTO) -> ResearchOwnerFullDTO:
        owner = await self._database_repository.owner_repo().short.get_owner_by_service_id(
            service_id=owner_dto.service_owner_id)

        # TODO Сделать нормальную авторизациб и аутентификацию для того тчобы создовать иследования
        # ЕЩПроблема с созданием овнера получение его сервиса
        if not owner:
            owner = await self._database_repository.owner_repo().short.add_owner(values=owner_dto.dict())
        return owner

    # TODO Выдвать клиента только в случае если нет данных от пользователя какого клиента выдовать
    async def _get_telegram_client(self) -> TelegramClientDTOGet:
        clients = [client for client in await self._database_repository.client_repo.get_all() if client.session_string]
        return clients[-1] if clients else None

    @staticmethod
    def _create_research_dto(research: ResearchDTOPost, owner: Any,
                             telegram_client: TelegramClientDTOGet) -> ResearchDTOBeDb:
        return ResearchDTOBeDb(

            owner_id=owner.owner_id,
            telegram_client_id=telegram_client.client_id,
            **research.dict()
        )

    async def _save_new_research(self, research_dto: ResearchDTOBeDb) -> ResearchDTOFull:
        return await self._database_repository.research_repo.short.save_new_research(
            values=research_dto.dict(exclude={'examinees_ids', 'examinees_user_names'})
        )

    async def _get_saved_research(self, research_id: int) -> ResearchDTORel:
        return await self._database_repository.research_repo.full.get_research_by_id(research_id=research_id)

    async def _add_users_to_research(self, research, telegram_client: TelegramClientDTOGet) -> Optional[
        List[UserDTOFull]]:
        users_dto = []

        # Если есть `examinees_user_names`, получить информацию о пользователях
        if research.examinees_user_names is not None:
            user_info = await self._collect_user_information_ids(telegram_client, research)
            if user_info:
                # Создаем объекты UserDTO, используя полученную информацию
                users_dto.extend(UserDTO(tg_user_id=user.tg_user_id, username=user.username) for user in user_info)

        # Добавляем объекты UserDTO на основе examinees_ids, если были переданы
        if research.examinees_ids:
            users_dto.extend(UserDTO(tg_user_id=tg_user_id) for tg_user_id in research.examinees_ids)

        # Добавляем пользователей в базу данных
        try:
            return await self._database_repository.user_in_research_repo.short.add_many_users(
                values=[user.dict() for user in users_dto]
            )
        except Exception as e:
            raise e

    async def _collect_user_information_ids(self, telegram_client: TelegramClientDTOGet, research: ResearchDTOPost) -> \
            Optional[List[UserDTO]]:
        if not research.examinees_user_names:
            return None

        users: List[UserDTOBase] = [UserDTOBase(username=name) for name in research.examinees_user_names]
        users_info = await self._information_collector.collect_users_information(
            users=users,
            client=telegram_client
        )
        return users_info

    async def _bind_users_to_research(self, research_id: int, research: ResearchDTOPost) -> None:
        db_users_ids = []  # Список для хранения user_id

        if research.examinees_ids:
            users_by_ids = await self._database_repository.user_in_research_repo.short.get_many_user_ids_by_telegram_ids(
                telegram_ids=research.examinees_ids
            )
            db_users_ids.extend(users_by_ids)

        if research.examinees_user_names:
            users_by_usernames = await self._database_repository.user_in_research_repo.short.get_many_user_ids_by_usernames(
                usernames=research.examinees_user_names
            )
            db_users_ids.extend(users_by_usernames)

        # Привязываем пользователей к исследованию
        for user_id in db_users_ids:
            await self._database_repository.user_in_research_repo.short.bind_research(
                user_id=user_id,
                research_id=research_id
            )
