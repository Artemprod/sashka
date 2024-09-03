import datetime
from typing import Optional, List
from sqlalchemy import select, insert

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

            #TODO конвертация в модель
            return new_client

    async def get_client_by_id(self, client_id: int) -> Optional[ClientModel]:
        async with self.db_session_manager.async_session_factory() as session:
            query = select(ClientModel).where(ClientModel.id == client_id)
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


    async def update(self, client: ClientModel) -> bool:
        async with self.db_session_manager.async_session_factory() as session:
            entity = await session.get(ClientModel, client.id)
            if not entity:
                return False
            for key, value in client.__dict__.items():
                if key != '_sa_instance_state':  # Пропускаем системное свойство SQLAlchemy
                    setattr(entity, key, value)
            await session.commit()
            return True

    async def delete(self, name: str) -> bool:
        async with self.db_session_manager.session_scope() as session_scope:
            instance = await session_scope.get(ClientModel, name)
            if instance:
                await session_scope.delete(instance)
                await session_scope.commit()
                return True
            return False



class ClientRepositoryFullModel(BaseRepository):
    ...