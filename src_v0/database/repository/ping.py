import datetime
from typing import Optional, List

from aiocache import cached, Cache
from sqlalchemy import select, insert, update, delete

from src_v0.database.postgres.models.ping import PingPrompt
from src_v0.database.repository.base import BaseRepository


# TODO Добавить обработчик try excrpt
class PingPromptRepository(BaseRepository):

    async def save_new_ping_prompt(self, values: dict) -> PingPrompt:
        async with (self.db_session_manager.async_session_factory() as session):
            stmt = insert(PingPrompt).values(**values).returning(PingPrompt)
            execution = await session.execute(stmt)
            await session.commit()
            new_ping_prompt = execution.scalars().first()

            # TODO конвертация в модель
            return new_ping_prompt

    @cached(ttl=300, cache=Cache.MEMORY)
    async def get_ping_prompt_by_order_number(self, ping_order_number: int) -> PingPrompt:
        async with (self.db_session_manager.async_session_factory() as session):
            async with session.begin():  # использовать транзакцию
                query = (select(PingPrompt).filter(PingPrompt.ping_order_number == ping_order_number))
                execute = await session.execute(query)
                ping_prompt = execute.scalars().first()
                return ping_prompt
