import pytest

from src.database.postgres import ResearchStatusEnum
from src.schemas.service.status import ResearchStatusDTO
from src.services.research.telegram.inspector import ResearchStarter


@pytest.fixture(scope="function")
async def research_starter(repo_storage, publisher) -> ResearchStarter:
    yield ResearchStarter(repo_storage, publisher)


class TestResearchStarter:
    @pytest.mark.parametrize(
        "research_id, expected_status",
        [(1, ResearchStatusEnum.IN_PROGRESS.name),
         (2, ResearchStatusEnum.IN_PROGRESS.name),
         (3, ResearchStatusEnum.IN_PROGRESS.name)]
    )
    @pytest.mark.asincio
    async def test_start_up_research(self, research_starter, research_id, expected_status):
        research = await research_starter.start_up_research(research_id)
        status: ResearchStatusDTO = await research_starter.repository.status_repo.research_status.get_research_status(
            research_id)
        assert status.status_name == expected_status
