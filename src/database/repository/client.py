import datetime
from typing import Optional, List
from sqlalchemy import select

from src.database.postgres.models.client import Client as ClientModel
from src.database.repository.base import BaseRepository


# TODO Добавить обработчик try excrpt
class ClientRepository(BaseRepository):

    async def save(self, name: str,
                   api_id: str,
                   api_hash: str,
                   app_version: Optional[str],
                   device_model: Optional[str],
                   system_version: Optional[str],
                   lang_code: Optional[str],
                   test_mode: Optional[bool],
                   session_string: Optional[str],
                   phone_number: Optional[str],
                   password: Optional[str],
                   parse_mode: Optional[str],
                   workdir: Optional[str],
                   created_at: datetime = datetime.datetime.now()) -> ClientModel:

        async with self.db_session_manager.session_scope() as session_scope:
            client = ClientModel(
                name=name,
                api_id=api_id,
                api_hash=api_hash,
                app_version=app_version,
                device_model=device_model,
                system_version=system_version,
                lang_code=lang_code,
                test_mode=test_mode,
                session_string=session_string,
                phone_number=phone_number,
                password=password,
                parse_mode=parse_mode,
                workdir=workdir,
                created_at=created_at
            )
            session_scope.add(client)
            await session_scope.commit()
            return client

    async def get_client_by_id(self, client_id: int) -> Optional[ClientModel]:
        async with self.db_session_manager.session_scope() as session_scope:
            query = select(ClientModel).where(ClientModel.id == client_id)
            results = await session_scope.execute(query)
            result = results.scalars().first()
            return result

    async def get_client_by_name(self, name: str) -> Optional[ClientModel]:
        async with self.db_session_manager.session_scope() as session_scope:
            query = select(ClientModel).where(ClientModel.name == name)
            results = await session_scope.execute(query)
            result = results.scalars().first()
            return result

    async def get_all(self) -> List[ClientModel]:
        async with self.db_session_manager.session_scope() as session_scope:
            query = select(ClientModel)
            results = await session_scope.execute(query)
            all_results = results.scalars().all()
            return all_results

    # Здесь можно оставить передачу объекта, так как это обеспечит целостность данных
    async def update(self, client: ClientModel) -> bool:
        async with self.db_session_manager.session_scope() as session_scope:
            entity = await session_scope.get(ClientModel, client.id)
            if not entity:
                return False
            for key, value in client.__dict__.items():
                if key != '_sa_instance_state':  # Пропускаем системное свойство SQLAlchemy
                    setattr(entity, key, value)
            await session_scope.commit()
            return True

    async def delete(self, name: str) -> bool:
        async with self.db_session_manager.session_scope() as session_scope:
            instance = await session_scope.get(ClientModel, name)
            if instance:
                await session_scope.delete(instance)
                await session_scope.commit()
                return True
            return False
