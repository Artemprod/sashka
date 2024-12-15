import pytest

from src.database.repository.storage import RepoStorage
from src.services.research.telegram.inspector import  ResearchStopper, UserDoneStopper


@pytest.fixture
def load_repository(mocker):
    return mocker.Mock(spec=RepoStorage)

@pytest.fixture
def load_stopper(mocker):
    return mocker.Mock(spec=ResearchStopper)

@pytest.fixture
def load_user_done(load_repository,load_stopper)->UserDoneStopper:
    instance = UserDoneStopper(repository=load_repository,stopper=load_stopper)
    instance.settings['delay_check_interval'] = 0.1
    return instance



