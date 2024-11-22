import os
import shutil
from pathlib import Path

import pytest
from pyrogram import Client

from src.dispatcher.communicators.consol import ConsoleCommunicator

test_phone = "9996601212"
test_password = "89671106966"
api_id = "23823287"
api_has = "fe561473a06737cb358db923e05e7868"


@pytest.fixture
async def init_client():
    session_path = Path(__file__).parent.joinpath("session_files").joinpath("test.session")

    app = Client(name=str(session_path.absolute()), api_id=api_id, api_hash=api_has, test_mode=True,
                 phone_number=test_phone,
                 password=test_password)
    yield app


@pytest.fixture
def get_console_communicator():
    return ConsoleCommunicator()


@pytest.fixture
def session_folder():
    folder_path = "./session_files/"
    # Создание новой папки
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # Возвращаем путь к папке, если нужно использовать его в тестах
    yield os.path.abspath(folder_path)
    # Дополнительная очистка после тестов, если нужно
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
