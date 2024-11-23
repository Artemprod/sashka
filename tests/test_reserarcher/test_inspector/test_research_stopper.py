import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from src.database.postgres import ResearchStatusEnum, Research


@pytest.mark.asyncio
class TestResearchStopper:
    @pytest.mark.parametrize(
        "research_id, expected_status",
        [(1, ResearchStatusEnum.DONE.name),
         (2, ResearchStatusEnum.DONE.name),
         (3, ResearchStatusEnum.DONE.name)]
    )
    async def test_complete_research(self, init_db, research_id, research_stopper, expected_status, repo_storage):
        research = await research_stopper.complete_research(research_id)
        async with repo_storage.assistant_repo.db_session_manager.async_session_factory() as session:
            async with session.begin():
                query = (select(Research).filter(Research.research_id == research_id).options(
                    joinedload(Research.status)
                ))
                execute = await session.execute(query)
                research = execute.scalars().first()
                assert research.status.status_name.name == expected_status
