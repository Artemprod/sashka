from pyrogram.utils import ainput

#TODO Сделать проперти с выдачей информации по назначению каждого коммуникатора
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

#TODO Описать функционал каждого коммуниктора доки для доавения в реестр
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

    async def get_code(self):
        code = await ainput("Code: ")
        return code

    async def send_error(self, message):
        print(message)
