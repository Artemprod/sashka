from typing import Optional, List
from sqlalchemy import select, insert, update, delete

from src.schemas.service.client import TelegramClientDTO
from src_v0.database.exceptions.create import ObjectWasNotCreated
from src_v0.database.exceptions.read import ObjectDoesNotExist, EmptyTableError
from src_v0.database.postgres.models.client import TelegramClient as ClientModel
from src_v0.database.repository.base import BaseRepository


# TODO Добавить обработчик try excrpt
class ClientRepository(BaseRepository):

    async def save(self, values: dict) -> Optional[TelegramClientDTO]:
        async with (self.db_session_manager.async_session_factory() as session):
            stmt = insert(ClientModel).values(**values).returning(ClientModel)
            execution = await session.execute(stmt)
            await session.commit()
            new_client = execution.scalars().first()
            # DONE конвертация в модель
            if new_client:
                return TelegramClientDTO.model_validate(new_client, from_attributes=True)
            else:
                raise ObjectWasNotCreated(orm_object=ClientModel.__name__,
                                          msg=f"object with this values {values} was not created")

    async def get_client_by_id(self, client_id: int) -> Optional[TelegramClientDTO]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.telegram_client_id == client_id)
            results = await session.execute(query)
            result = results.scalars().first()
            # DONE конвертация в модель
            if result:
                return TelegramClientDTO.model_validate(result, from_attributes=True)
            else:
                raise ObjectDoesNotExist(orm_object=ClientModel.__name__, msg=f"client with id {client_id} not found")




    async def get_client_by_name(self, name: str) -> Optional[TelegramClientDTO]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.name == name)
            results = await session.execute(query)
            result = results.scalars().first()
            if result:
                return TelegramClientDTO.model_validate(result, from_attributes=True)
            else:
                raise ObjectDoesNotExist(orm_object=ClientModel.__name__, msg=f"client with name {name} not found")

    async def get_all(self) -> List[TelegramClientDTO]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel)
            results = await session.execute(query)
            all_results = results.scalars().all()
            if not all_results:
                raise EmptyTableError()
            else:
                return [TelegramClientDTO.model_validate(client, from_attributes=True) for client in all_results]

    async def update(self, telegram_client_id, values: dict) -> TelegramClientDTO:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = (update(ClientModel)
                        .where(ClientModel.telegram_client_id == telegram_client_id)
                        .values(**values)
                        .returning(ClientModel)
                        )
                execution = await session.execute(stmt)
                client = execution.scalar_one_or_none()
                # DONE Возвращать модель
                return TelegramClientDTO.model_validate(client, from_attributes=True)

    async def delete(self, name: str) -> bool:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = (delete(ClientModel)
                        .where(ClientModel.name == name)
                        .returning(ClientModel)
                        )
                deleted = await session.execute(stmt).scalar_one()
                session.commit()
                return deleted


class ClientRepositoryFullModel(BaseRepository):
    ...
