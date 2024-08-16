import abc


# паблишер отправляет в нужную очередь


class BasePublisher(abc.ABC):
    @abc.abstractmethod
    async def publish(self, *args, **kwargs):
        pass


class NATSPublisher(BasePublisher):

    def __init__(self):
        ...

    async def publish(self, message):
        ...
