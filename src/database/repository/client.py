from typing import List
from typing import Optional

from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update

from src.database.exceptions.create import ObjectWasNotCreated
from src.database.exceptions.read import EmptyTableError
from src.database.exceptions.read import NoFreeClientsError
from src.database.exceptions.read import ObjectDoesNotExist
from src.database.postgres import ResearchStatus
from src.database.postgres import ResearchStatusEnum
from src.database.postgres.models.client import TelegramClient as ClientModel
from src.database.postgres.models.research import Research
from src.database.repository.base import BaseRepository
from src.schemas.service.client import TelegramClientDTOGet
from src.services.cache.service import redis_cache_decorator


# TODO Добавить обработчик try excrpt
class ClientRepository(BaseRepository):
    async def save(self, values: dict) -> Optional[TelegramClientDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            stmt = insert(ClientModel).values(**values).returning(ClientModel)
            execution = await session.execute(stmt)
            await session.commit()
            new_client = execution.scalars().first()
            # DONE конвертация в модель
            if new_client:
                return TelegramClientDTOGet.model_validate(new_client, from_attributes=True)
            else:
                raise ObjectWasNotCreated(
                    orm_object=ClientModel.__name__, msg=f"object with this values {values} was not created"
                )

    @redis_cache_decorator(
        key="client:client_id:{client_id}",
    )
    async def get_client_by_id(self, client_id: int) -> Optional[TelegramClientDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.client_id == client_id)
            results = await session.execute(query)
            result = results.scalars().first()
            # DONE конвертация в модель
            if result:
                return TelegramClientDTOGet.model_validate(result, from_attributes=True)
            else:
                raise ObjectDoesNotExist(orm_object=ClientModel.__name__, msg=f"client with id {client_id} not found")

    # no cache this
    async def get_clients_by_research_id(self, research_id: str) -> Optional[List[TelegramClientDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.researches.any(Research.research_id == research_id))
            results = await session.execute(query)
            all_clients = results.scalars().all()
            if not all_clients:
                return None
            return [
                TelegramClientDTOGet.model_validate(client, from_attributes=True) for client in all_clients
            ]

    @redis_cache_decorator(
        key="client:name:{name}",
    )
    async def get_client_by_name(self, name: str) -> Optional[TelegramClientDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.name == name)
            results = await session.execute(query)
            result = results.scalars().first()
            if result:
                return TelegramClientDTOGet.model_validate(result, from_attributes=True)
            else:
                raise ObjectDoesNotExist(orm_object=ClientModel.__name__, msg=f"client with name {name} not found")

    @redis_cache_decorator(
        key="client:telegram_id:{telegram_id}",
    )
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[list[TelegramClientDTOGet]]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.telegram_client_id == telegram_id)
            results = await session.execute(query)
            result = results.scalars().all()
            if result:
                return [TelegramClientDTOGet.model_validate(client, from_attributes=True) for client in result]
            else:
                raise ObjectDoesNotExist(
                    orm_object=ClientModel.__name__, msg=f"client with research_id {telegram_id} not found"
                )

    @redis_cache_decorator(
        key="client:all",
    )
    async def get_all(self) -> List[TelegramClientDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel)
            results = await session.execute(query)
            all_results = results.scalars().all()
            if not all_results:
                raise EmptyTableError()
            else:
                return [TelegramClientDTOGet.model_validate(client, from_attributes=True) for client in all_results]

    async def get_clients_ready_for_research(self) -> List[TelegramClientDTOGet]:
        async with self.db_session_manager.async_session_factory() as session:
            # Запрос клиентов, участвующих в исследованиях
            client_in_research_query = (
                select(Research.telegram_client_id)
                .join(Research.status)
                .where(ResearchStatus.status_name == ResearchStatusEnum.IN_PROGRESS)
                .distinct()
            )

            # Выполняем запрос клиентов в исследованиях
            in_research_result = await session.execute(client_in_research_query)
            clients_in_research = set(in_research_result.scalars().all())

            # Запрос клиентов, не участвующих в исследованиях
            clients_query = select(ClientModel).where(ClientModel.client_id.notin_(clients_in_research))

            # Выполняем запрос всех клиентов, не участвующих в исследованиях
            all_clients_result = await session.execute(clients_query)
            ready_clients = [
                TelegramClientDTOGet.model_validate(client) for client in all_clients_result.scalars().all()
            ]

            if not ready_clients:
                raise NoFreeClientsError()

            return ready_clients

    async def update(self, telegram_client_id, values: dict) -> TelegramClientDTOGet:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = (
                    update(ClientModel)
                    .where(ClientModel.telegram_client_id == telegram_client_id)
                    .values(**values)
                    .returning(ClientModel)
                )
                execution = await session.execute(stmt)
                client = execution.scalar_one_or_none()
                # DONE Возвращать модель
                return TelegramClientDTOGet.model_validate(client, from_attributes=True)

    async def delete(self, name: str) -> bool:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = delete(ClientModel).where(ClientModel.name == name).returning(ClientModel)
                deleted = await session.execute(stmt).scalar_one()
                session.commit()
                return deleted


class ClientRepositoryFullModel(BaseRepository): ...
