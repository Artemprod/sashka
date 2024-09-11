import datetime
from typing import Optional, List
from sqlalchemy import select, insert, update, delete

from src.database.postgres.models.client import TelegramClient as ClientModel
from src.database.repository.base import BaseRepository


# TODO Добавить обработчик try excrpt
class ClientRepository(BaseRepository):

    async def save(self, values: dict) -> ClientModel:
        async with (self.db_session_manager.async_session_factory() as session):
            stmt = insert(ClientModel).values(**values).returning(ClientModel)
            execution = await session.execute(stmt)
            await session.commit()
            new_client = execution.scalars().first()

            # TODO конвертация в модель
            return new_client

    async def get_client_by_id(self, client_id: int) -> Optional[ClientModel]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.telegram_client_id == client_id)
            results = await session.execute(query)
            result = results.scalars().first()
            # TODO конвертация в модель
            return result



    async def get_client_by_name(self, name: str) -> Optional[ClientModel]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.name == name)
            results = await session.execute(query)
            result = results.scalars().first()
            return result

    async def get_all(self) -> List[ClientModel]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel)
            results = await session.execute(query)
            all_results = results.scalars().all()
            return all_results

    async def update(self, telegram_client_id, values: dict) -> bool:
        async with self.db_session_manager.async_session_factory() as session:
            async with session.begin():  # использовать транзакцию
                stmt = (update(ClientModel)
                        .where(ClientModel.telegram_client_id == telegram_client_id)
                        .values(**values)
                        .returning(ClientModel)
                        )
                execution = await session.execute(stmt)
                client = execution.scalar_one_or_none()
                # #TODO Возвращать модель
                return client

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
