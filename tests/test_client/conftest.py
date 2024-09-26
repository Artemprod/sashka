import os
import shutil

import pytest
from environs import Env
from pyrogram import Client

from src_v0.dispatcher.communicators.reggestry import ConsoleCommunicator

test_phone = "9996601212"
test_password = "89671106966"
api_id = "23823287"
api_has = "fe561473a06737cb358db923e05e7868"


@pytest.fixture
async def init_client():
    env = Env()
    env.read_env('.env')
    session_path = r"D:\projects\AIPO_V2\CUSTDEVER\tests\test_client\session_files\test.session"
    app = Client(name=session_path, api_id=api_id, api_hash=api_has,
                 phone_number=test_phone,
                 password=test_password,
                 test_mode=True)
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

