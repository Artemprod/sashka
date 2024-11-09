

from configs.redis import telegram_redis_getter_config
from src.dispatcher import BaseCommunicator
from src.dispatcher.interactions.code import RedisTelegramGetter


# TODO Вывнести код геттер в интерфес и подумать над диспетчеразацией
# TODO Добавить деораторы для отлова ошибок ( написать класс методы которых отлов ошибок )

class TelegramCommunicator(BaseCommunicator):
    registry_key = "telegram"

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.code_getter = RedisTelegramGetter(settings=telegram_redis_getter_config)
        self._user_id = user_id

    async def get_code(self) -> str:
        return await self.code_getter.get_code(self._user_id)

    async def recovery_code(self) -> str:
        return await self.code_getter.get_recovery_code(self._user_id)

    async def enter_phone_number(self) -> str:
        return await self.code_getter.get_phone_number(self._user_id)

    async def enter_cloud_password(self) -> str:
        return await self.code_getter.get_cloud_password(self._user_id)

    async def confirm(self) -> str:
        return await self.code_getter.get_confirmation(self._user_id)

    async def first_name(self) -> str:
        return await self.code_getter.get_first_name(self._user_id)

    async def last_name(self) -> str:
        return await self.code_getter.get_last_name(self._user_id)

    async def send_error(self):
        # TODO: Внедрить нотификатор для отправки сообщения пользователю
        ...







