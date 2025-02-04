import pytest

from src.database.repository.storage import RepoStorage
from src.services.research.telegram.inspector import ResearchOverChecker, ResearchStopper


@pytest.fixture(scope="module", autouse=True)
def load_repository(mocker):
    return mocker.Mock(spec=RepoStorage)


@pytest.fixture(scope="module", autouse=True)
def load_research_stopper(load_repository) -> ResearchStopper:
    return ResearchStopper(repository=load_repository)
