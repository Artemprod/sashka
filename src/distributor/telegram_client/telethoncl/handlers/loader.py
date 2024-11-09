import importlib.util
import inspect
import os

from loguru import logger


def is_handler(func):
    """Проверяет, является ли функция хендлером для событий Telethon"""
    # Возможно, шел типовой атрибут
    expected_attribute_name = '__tl.handlers'

    if hasattr(func, expected_attribute_name):
        logger.info(f"Function {func.__name__} is considered a handler.")
        return True
    else:
        logger.warning(f"Function {func.__name__} is NOT recognized as a handler.")
    return False


def collect_handlers_from_module(module):
    """Собирает хендлеры из модуля"""
    logger.info(f"Collecting handlers from module: {module.__name__}")
    handlers = [
        obj for name, obj in inspect.getmembers(module)
        if inspect.isfunction(obj) and is_handler(obj)
    ]
    return handlers


def load_module_from_path(path):
    """Импортирует модуль по пути"""
    module_name = os.path.splitext(os.path.basename(path))[0]
    logger.info(f"Loading module: {module_name} from path: {path}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_handlers_in_directories(directories):
    """Рекурсивно ищет все модули в директориях и собирает хендлеры"""
    all_handlers = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_path = os.path.join(root, file)
                    module = load_module_from_path(module_path)
                    handlers = collect_handlers_from_module(module)
                    all_handlers.extend(handlers)
    return all_handlers
