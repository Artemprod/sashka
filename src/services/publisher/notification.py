from abc import ABC
from abc import abstractmethod


class BaseNotificator(ABC):
    @abstractmethod
    async def notify_completion(self, *args, **kwargs):
        pass

    @abstractmethod
    async def handle_incomplete_research(self, *args, **kwargs):
        pass


class TelegramNotificator(BaseNotificator):
    async def notify_completion(self, *args, **kwargs):
        print("Отправил уведомление в телеграм ")
        pass

    async def handle_incomplete_research(self, *args, **kwargs):
        print("Отправил уведомление в телеграм ")
        pass
