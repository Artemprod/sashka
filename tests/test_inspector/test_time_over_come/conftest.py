import pytest

from src.database.repository.storage import RepoStorage
from src.services.research.telegram.inspector import ResearchOverChecker, ResearchStopper


@pytest.fixture(scope="module", autouse=True)
def load_repository(mocker):
    return mocker.Mock(spec=RepoStorage)

@pytest.fixture(scope="module", autouse=True)
def load_stopper(mocker):
    return mocker.Mock(spec=ResearchStopper)

@pytest.fixture(scope="module", autouse=True)
def load_time_stopper(load_repository,load_stopper)->ResearchOverChecker:
    instance = ResearchOverChecker(repository=load_repository,stopper=load_stopper)
    instance.settings['delay_check_interval'] = 0.1
    return instance



