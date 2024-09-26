import pytest

from src_v0.dispatcher.communicators.reggestry import ConsoleCommunicator


@pytest.fixture(scope="package")
def get_console_communicator():
    return ConsoleCommunicator()
