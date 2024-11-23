import pytest

from src.services.research.telegram.inspector import ResearchProcess


@pytest.fixture(scope="function")
async def research_process(repo_storage, publisher):
    yield ResearchProcess(repo_storage, notifier=None, publisher=publisher)


@pytest.mark.asyncio
class TestResearchProcess:
    # TODO: Add more tests and how to check result
    @pytest.mark.parametrize("research_id", [1, 2, 3])
    async def test_process(self, research_process, research_id):
        # await research_process.run(research_id)
        assert True
