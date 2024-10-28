from src.dispatcher.communicators.consol import ConsoleCommunicator
from src.dispatcher.communicators.email import EmailCommunicator
from src.dispatcher.communicators.reggestry import CommunicatorRegistryBase
from src.dispatcher.communicators.telegram import TelegramCommunicator


# Класс диспетчера
# class CommunicatorDispatcher:
#     def __init__(self, service_name, *args, **kwargs):
#         # Извлекаем фабрику из реестра и создаем экземпляр с аргументами
#         self.service_instance = CommunicatorRegistryBase.get_registry()[service_name](*args, **kwargs)
#
#     def __getattr__(self, item):
#         # Проксируем вызовы атрибутов к экземпляру сервиса
#         return getattr(self.service_instance, item)

# class CommunicatorDispatcher:
#     def __new__(cls, service_name: str, *args, **kwargs):
#         registry = CommunicatorRegistryBase.get_registry()
#         if service_name not in registry:
#             raise ValueError(f"Service '{service_name}' not found in registry.")
#
#         # Создаем экземпляр нужного класса напрямую
#         instance = registry[service_name](*args, **kwargs)
#
#         # Возвращаем созданный экземпляр вместо класса CommunicatorDispatcher
#         return instance
#

class CommunicatorDispatcher:
    # Словарь доступных коммуникаторов
    COMMUNICATORS = {
        "telegram": TelegramCommunicator,
        "console": ConsoleCommunicator,
        "email": EmailCommunicator
    }

    def __init__(self, service_name):
        self.service_name = service_name

    def get_communicator(self, *args, **kwargs):
        communicator = self.COMMUNICATORS.get(self.service_name)
        if communicator is None:
            raise ValueError(f"No service {self.service_name}")
        return communicator(*args, **kwargs)

# communicator = CommunicatorDispatcher(service_name=service_type, telegram_user_id=service_dto.service_data.user_id)