import pytest
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.inspector import UserPingator


@pytest.fixture(scope="function", autouse=True)
def load_publisher(mocker):
    return mocker.Mock(spec=NatsPublisher)


@pytest.fixture(scope="function", autouse=True)
def load_pingator(load_repository, load_publisher) -> UserPingator:
    instance = UserPingator(repo=load_repository, publisher=load_publisher)
    return instance
