import datetime
from functools import wraps
from typing import Any, Callable
from typing import List
from typing import Optional

from loguru import logger
from sqlalchemy.exc import IntegrityError

from src.database.postgres.models.enum_types import ResearchStatusEnum
from src.database.postgres.models.enum_types import UserStatusEnum
from src.database.repository.storage import RepoStorage
from src.schemas.service.client import TelegramClientDTOGet
from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.owner import ResearchOwnerFullDTO
from src.schemas.service.research import ResearchDTOBeDb
from src.schemas.service.research import ResearchDTOFull
from src.schemas.service.research import ResearchDTOPost
from src.schemas.service.research import ResearchDTORel
from src.schemas.service.user import UserDTO
from src.schemas.service.user import UserDTOBase
from src.schemas.service.user import UserDTOFull
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.research.base import BaseResearchManager
from src.services.research.telegram.decorators.reserach_creatoe import unique_users_in_research


# TODO переделать класс вынести в отдельные классы сущности ресерч создатель иследования и тд разные стратегии
class TelegramResearchManager(BaseResearchManager):
    def __init__(self, repository: RepoStorage, information_collector: TelegramUserInformationCollector):
        self._database_repository = repository
        self._information_collector = information_collector

    # TODO оптимизировать метод
    # TODO Вытащить создание овнера наружу из класса
    @unique_users_in_research
    async def create_research(self, research: ResearchDTOPost, owner: ResearchOwnerDTO) -> ResearchDTORel:
        """Создает исследование в базе данных и назначает необходимые данные."""
        try:
            # Создаем овнера в базе, если нет
            owner = await self._create_new_owner(owner_dto=owner)
            # Получаем telegram клиента
            telegram_client: TelegramClientDTOGet = await self._get_telegram_client(
                client_id=research.telegram_client_id
            )
            # Создать и сохранить исследование
            research_dto: ResearchDTOBeDb = self._create_research_dto(research, owner)
            db_research: ResearchDTOFull = await self._save_new_research(research_dto)
            # Установить статус для исследования
            await self._set_research_status(db_research)
            # Собираем данные о пользователях
            user_info: Optional[List[UserDTO]] = await self._collect_user_info(telegram_client, research)
            # Добавляем пользователей в исследование
            await self._add_users_to_research(users_dto=user_info)
            # Установить статусы для пользователей
            await self._set_user_status(research=research)
            # Связать пользователей с исследованием
            await self._bind_users_to_research(research_id=db_research.research_id, research=research)
            # Возврат DTO с сохраненным исследованием
            saved_research: ResearchDTORel = await self._get_saved_research(db_research.research_id)
            return saved_research

        except Exception as e:
            logger.error(f"Error during research creation: {e} \n {e.args}")
            raise

    async def get_research_info(self, research: ResearchDTOPost):
        full_info = await self._database_repository.research_repo.full.get_research_by_id(
            research_id=research.research_id
        )
        logger.info(f"Вот полная инфа {full_info}")
        return full_info

    async def _set_research_status(self, db_research: ResearchDTOFull):
        await self._database_repository.status_repo.research_status.add_research_status(
            values={
                "research_id": db_research.research_id,
                "status_name": ResearchStatusEnum.WAIT,
                "created_at": datetime.datetime.now(),
            }
        )

    async def _set_user_status(self, research: ResearchDTOPost) -> None:
        """Устанавливает статус пользователей и возвращает список пользователей, для которых статус не был установлен."""
        db_users = set()

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
            service_id=owner_dto.service_owner_id
        )

        # TODO Сделать нормальную авторизациб и аутентификацию для того тчобы создовать иследования
        # ЕЩПроблема с созданием овнера получение его сервиса
        if not owner:
            owner = await self._database_repository.owner_repo().short.add_owner(values=owner_dto.dict())
        return owner

    # TODO Выдвать клиента только в случае если нет данных от пользователя какого клиента выдовать
    async def _get_telegram_client(self, client_id) -> TelegramClientDTOGet:
        client: TelegramClientDTOGet = await self._database_repository.client_repo.get_client_by_id(client_id=client_id)
        return client

    @staticmethod
    def _create_research_dto(research: ResearchDTOPost, owner: Any) -> ResearchDTOBeDb:
        return ResearchDTOBeDb(owner_id=owner.owner_id, **research.model_dump())

    async def _save_new_research(self, research_dto: ResearchDTOBeDb) -> ResearchDTOFull:
        return await self._database_repository.research_repo.short.save_new_research(
            values=research_dto.model_dump(exclude={"examinees_user_names"})
        )

    async def _get_saved_research(self, research_id: int) -> ResearchDTORel:
        return await self._database_repository.research_repo.full.get_research_by_id(research_id=research_id)

    async def _collect_user_info(self, telegram_client, research):
        users_dto = []
        try:
            # Если есть `examinees_user_names`, получить информацию о пользователях
            if research.examinees_user_names is not None:
                print()
                user_info: Optional[List[UserDTO]] = await self._collect_user_information_ids(telegram_client, research)
                if user_info:
                    # Создаем объекты UserDTO, используя полученную информацию
                    users_dto.extend(user_info)
            return users_dto
        except Exception as e:
            raise e

    async def _add_users_to_research(self, users_dto: [List[UserDTO]]) -> Optional[List[UserDTOFull]]:
        # Добавляем пользователей в базу данных
        try:
            return await self._database_repository.user_in_research_repo.short.add_many_users(
                values=[user.model_dump() for user in users_dto]
            )
        except Exception as e:
            raise e

    async def _collect_user_information_ids(
        self, telegram_client: TelegramClientDTOGet, research: ResearchDTOPost
    ) -> Optional[List[UserDTO]]:
        if not research.examinees_user_names:
            return

        users: List[UserDTOBase] = [UserDTOBase(username=name) for name in research.examinees_user_names]
        users_info: Optional[List[UserDTO]] = await self._information_collector.collect_users_information(
            users=users, client=telegram_client
        )
        return users_info

    async def _bind_users_to_research(self, research_id: int, research: ResearchDTOPost) -> None:
        db_users_ids = []  # Список для хранения user_id

        if research.examinees_user_names:
            users_by_usernames = (
                await self._database_repository.user_in_research_repo.short.get_many_user_ids_by_usernames(
                    usernames=research.examinees_user_names
                )
            )
            db_users_ids.extend(users_by_usernames)

        # Привязываем пользователей к исследованию
        for user_id in db_users_ids:
            await self._database_repository.user_in_research_repo.short.bind_research(
                user_id=user_id, research_id=research_id
            )
