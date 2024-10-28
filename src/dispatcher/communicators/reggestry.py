from pyrogram.utils import ainput


# TODO Сделать проперти с выдачей информации по назначению каждого коммуникатора
class CommunicatorRegistryBase(type):
    REGISTRY = {}

    def __new__(cls, name, bases, attrs):
        new_cls = super(CommunicatorRegistryBase, cls).__new__(cls, name, bases, attrs)
        # Если это не базовый класс, сохраняем фабрику для создания экземпляров
        if not attrs.get('is_base_class', False):
            registry_key = attrs.get('registry_key', name.lower())
            cls.REGISTRY[registry_key] = new_cls
        return new_cls

    @classmethod
    def get_registry(cls):
        return dict(cls.REGISTRY)





# TODO Описать функционал каждого коммуниктора доки для доавения в реестр
# Базовый класс который будет использовать метакласс RegistryBase
class BaseCommunicator(metaclass=CommunicatorRegistryBase):
    is_base_class = True

    def __init__(self, *args, **kwargs):
        pass

    async def get_code(self, *args, **kwargs) -> str:
        raise NotImplemented

    async def recovery_code(self, *args, **kwargs):
        raise NotImplemented

    async def enter_phone_number(self, *args, **kwargs):
        raise NotImplemented

    async def enter_cloud_password(self, *args, **kwargs):
        raise NotImplemented

    async def confirm(self, *args, **kwargs):
        raise NotImplemented

    async def first_name(self, *args, **kwargs):
        raise NotImplemented

    async def last_name(self, *args, **kwargs):
        raise NotImplemented

    async def send_error(self, *args, **kwargs):
        raise NotImplemented


class BotCommunicator(BaseCommunicator):
    registry_key = "telegram"

    def __init__(self):
        self.bot_token = None
