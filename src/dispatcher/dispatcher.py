from src.dispatcher.communicators.consol import ConsoleCommunicator

from src.dispatcher.communicators.telegram import TelegramCommunicator

#TODO передаелать этот контенер под диспетчера

# class CommunicatorDispatcher:
#     instruments = {}
#
#     def __init__(self, cls):
#         self(cls)
#
#     def __call__(self, cls):
#         # Добавляем класс в словарь по ключу type
#         if hasattr(cls, 'type'):
#             self.instruments[cls.type] = cls
#         else:
#             raise AttributeError("Class does not have 'type' attribute.")
#         # Возвращаем класс, чтобы декоратор не изменял его
#         return cls


class CommunicatorDispatcher:
    # Словарь доступных коммуникаторов
    COMMUNICATORS = {
        "telegram": TelegramCommunicator,
        "console": ConsoleCommunicator,

    }

    def __init__(self, service_name):
        self.service_name = service_name

    def get_communicator(self, *args, **kwargs):
        communicator = self.COMMUNICATORS.get(self.service_name)
        if communicator is None:
            raise ValueError(f"No service {self.service_name}")
        return communicator(*args, **kwargs)

