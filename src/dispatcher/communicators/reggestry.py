from pyrogram.utils import ainput


# TODO Сделать проперти с выдачей информации по назначению каждого коммуникатора
class CommunicatorRegistryBase(type):
    REGISTRY = {}

    def __new__(cls, name, bases, attrs):
        new_cls = super(CommunicatorRegistryBase, cls).__new__(cls, name, bases, attrs)
        # Если это не базовый класс, добавляем в реестр
        if not attrs.get('is_base_class', False):
            registry_key = attrs.get('registry_key', name.lower())
            cls.REGISTRY[registry_key] = new_cls()

        return new_cls

    @classmethod
    def get_registry(cls):
        return dict(cls.REGISTRY)


# TODO Описать функционал каждого коммуниктора доки для доавения в реестр
# Базовый класс который будет использовать метакласс RegistryBase
class BaseCommunicator(metaclass=CommunicatorRegistryBase):
    is_base_class = True

    async def get_code(self, *args, **kwargs) -> str:
        raise NotImplemented

    async def send_error(self, *args, **kwargs):
        raise NotImplemented


class BotCommunicator(BaseCommunicator):
    registry_key = "bot"

    def __init__(self):
        self.bot_token = None


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
    async def enter_password() -> str:
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
