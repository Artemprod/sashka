from fastapi import HTTPException
from sqlalchemy import select

from src.database.postgres import Configuration
from src.database.repository.base import BaseRepository
from src.web.models.configuration import ConfigurationCreateSchema, ConfigurationSchema


class ConfigurationRepository(BaseRepository):

    async def create_or_update(self, values: ConfigurationCreateSchema) -> ConfigurationSchema:
        '''
        Реализация паттерна singleton
        '''
        async with self.db_session_manager.async_session_factory() as session:
            existing_config = await session.execute(
                select(Configuration)
                .where(Configuration.configuration_id == 1)
            )
            config_instance = existing_config.scalars().first()

            if config_instance:
                [setattr(config_instance, key, value) for key, value in values.model_dump().items()]
            else:
                config_instance = Configuration(configuration_id=1, **values.model_dump())
                session.add(config_instance)

            await session.commit()
            await session.refresh(config_instance)

            return ConfigurationSchema.model_validate(config_instance,from_attributes=True)

    async def get(self) -> ConfigurationSchema:
        async with self.db_session_manager.async_session_factory() as session:
            existing_config = await session.execute(
                select(Configuration)
                .where(Configuration.configuration_id == 1)
            )
            config_instance = existing_config.scalars().first()
            #TODO вынести в API
            if not config_instance:
                raise HTTPException(status_code=404, detail="Configuration not found")

            return ConfigurationSchema.model_validate(config_instance,from_attributes=True)
