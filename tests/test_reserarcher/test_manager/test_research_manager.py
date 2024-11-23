import pytest
from sqlalchemy import text

from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.research import ResearchDTOPost
from src.services.parser.user.gather_info import TelegramUserInformationCollector
from src.services.research.telegram.manager import TelegramResearchManager
from .testdata import ResearchDTOPostCases, TEST_CASES


@pytest.fixture(scope="session")
async def telegram_user_information_collector(publisher):
    return TelegramUserInformationCollector(publisher)


@pytest.fixture(scope="session")
async def telegram_research_manager(init_db, repo_storage, telegram_user_information_collector):
    return TelegramResearchManager(repo_storage, telegram_user_information_collector)


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def truncate_researches(init_db):
    async with init_db.async_session_factory() as session:
        async with session.begin():
            trucate_stm = text("TRUNCATE researches CASCADE")
            await session.execute(trucate_stm)
            await session.commit()


@pytest.fixture(scope="session")
async def research(truncate_researches) -> ResearchDTOPost:
    return ResearchDTOPost(
        research_uuid="test_uuid",
        name='Test',
        title="Test title",
        theme="Test theme",
        descriptions="Test description",
        additional_information="Test additional information",
        assistant_id=1,  # в create test data указано, берем из него
        examinees_ids=[1, 2, 3],
        examinees_user_names=["test1", "test2", "test3"]
    )


@pytest.fixture(scope="session")
async def owner(repo_storage) -> ResearchOwnerDTO:
    return await repo_storage.owner_repo.short.get_owner_by_owner_id(1)


@pytest.mark.asyncio
class TestTelegramResearchManager:
    # TODO: добавить тесты для каждой функции в классе TelegramResearchManager
    @pytest.mark.parametrize(
        "test_case",
        [
            # pytest.param(test_case, id=test_case)
            test_case for test_case in TEST_CASES
        ]
    )
    async def test_create_research(
            self,
            repo_storage,
            telegram_research_manager,
            research,
            owner,
            test_case: ResearchDTOPostCases
    ):
        with test_case.expectation:
            research_id = await telegram_research_manager.create_research(test_case.research_dto, owner)
