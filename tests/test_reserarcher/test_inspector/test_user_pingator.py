import pytest

from src.services.research.telegram.inspector import UserPingator


@pytest.fixture(scope="session")
async def user_pingator(init_db, repo_storage, publisher):
    return UserPingator(repo_storage, publisher)


@pytest.mark.asyncio
class TestUserPingator:
    @pytest.mark.parametrize("research_id", [1, 2, 3])
    async def test_ping_user(self, user_pingator, research_id):
        # await user_pingator.ping_users(research_id)
        assert True
