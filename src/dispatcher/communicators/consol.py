from pyrogram.utils import ainput

from src.dispatcher import BaseCommunicator


class ConsoleCommunicator(BaseCommunicator):
    registry_key = "console"

    async def get_code(self) -> str:
        print("Работает коммуникактор")
        code = await ainput("Code: ")
        return code

    @staticmethod
    async def recovery_code() -> str:
        print("Работает коммуникактор")
        recovery_code = await ainput("recovery_code: ")
        return recovery_code

    @staticmethod
    async def enter_phone_number() -> str:
        print("Работает коммуникактор")
        phone_number = await ainput("phone_number: ")
        return phone_number

    @staticmethod
    async def enter_cloud_password() -> str:
        print("Работает коммуникактор")
        password = await ainput("password: ")
        return password

    @staticmethod
    async def confirm() -> str:
        print("Работает коммуникактор")
        confirm = await ainput("confirm (y/N): ")
        return confirm.lower()

    @staticmethod
    async def first_name() -> str:
        print("Работает коммуникактор")
        first_name = await ainput("first_name: ")
        return first_name

    @staticmethod
    async def last_name() -> str:
        print("Работает коммуникактор")
        last_name = await ainput("last_name: ")
        return last_name

    async def send_error(self, message):
        print(message)
