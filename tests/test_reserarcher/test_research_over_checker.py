import pytest

from src.services.research.telegram.inspector import ResearchOverChecker


@pytest.fixture(scope="function")
async def research_over_checker(repo_storage, research_stopper):
    return ResearchOverChecker(repo_storage, research_stopper)


class TestResearchOverChecker:
    # TODO 1: Implement the test_check_research_over method
    @pytest.mark.asyncio
    @pytest.mark.parametrize("research_id", [1, 2, 3])
    async def test_check_research_over(self, research_over_checker, research_id):
        # await research_over_checker.monitor_completion(research_id)
        assert True
