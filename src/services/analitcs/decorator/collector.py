class AnalyticCollector:
    instruments = {}

    def __init__(self, cls):
        self(cls)

    def __call__(self, cls):
        # Добавляем класс в словарь по ключу type
        if hasattr(cls, 'type'):
            self.instruments[cls.type] = cls
        else:
            raise AttributeError("Class does not have 'type' attribute.")
        # Возвращаем класс, чтобы декоратор не изменял его
        return cls

