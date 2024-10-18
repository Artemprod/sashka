import os.path

import pytest
from pyrogram import Client

from src.dispatcher.communicators.reggestry import BaseCommunicator
from src.distributor.telegram_client.pyro.client import Manager

from testdata import TEST_CASES, TestDataCases


class TestCommunicator(BaseCommunicator):
    registry_key = "test"

    def __init__(self, test_code=None):
        self.test_code = test_code

    async def get_code(self):
        return self.test_code

    async def send_error(self, message):
        print(message)


class TestManager:

    async def test_connection(self, init_client, session_folder):
        assert isinstance(init_client, Client)
        manager: Manager = Manager(init_client)
        await manager.connect_client()
        assert manager.app.is_connected == True, "Подключение не установлено"
        await manager.app.disconnect()

    # правильный кейс ✅
    # неправильный код ✅
    # неправильный номер телефона ✅
    # неправильный api hash ✅
    # неправильный api id ✅
    # неправильный облочный пароль✅
    # телфон забанен
    @pytest.mark.parametrize(
        "test_case",
        [
            pytest.param(test_case, id=test_case._id)
            for test_case in TEST_CASES
        ],
    )
    async def test_authorization(self,
                                 test_case: TestDataCases,
                                 session_folder
                                 ):
        session_path = os.path.normpath(str(os.path.join(session_folder, test_case.name)))
        app = Client(name=session_path, api_id=test_case.api_id, api_hash=test_case.api_hash, test_mode=True,
                     phone_number=test_case.test_phone, password=test_case.test_password, autorization_callback=None)
        manager: Manager = Manager(app)
        manager.auth_attempts = 1
        with test_case.expectation:
            await manager.authorize(communicator=TestCommunicator(test_code=test_case.phone_code))
        await app.disconnect()
