
from typing import Callable

import asyncio
from functools import wraps


from apscheduler.events import (
    EVENT_SCHEDULER_STARTED,
    EVENT_SCHEDULER_SHUTDOWN,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED
)

from loguru import logger


def create_async_listener(func: Callable) -> Callable:
    """
    Декоратор для создания асинхронного слушателя событий.
    Запускает функцию в executor'е для избежания блокировки event loop.
    """

    @wraps(func)
    def wrapper(event):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, func, event)
    return wrapper



@create_async_listener
def handle_job_event(event) -> None:
    """Обработчик событий выполнения задач"""
    if event.code not in (EVENT_JOB_EXECUTED,EVENT_JOB_ERROR):
        return

    if event.exception:
        logger.warning(f"⚠️ Задача {event.job_id} завершилась с ошибкой: {event.exception}")
        raise event.exception
    logger.info(f"✅ Задача {event.job_id} успешно выполнена!")


@create_async_listener
def handle_scheduler_event(event) -> None:
    """Обработчик событий планировщика"""
    event_messages = {
        EVENT_SCHEDULER_STARTED: "🚀 Планировщик запущен!",
        EVENT_SCHEDULER_SHUTDOWN: "🛑 Планировщик остановлен!"
    }
    if message := event_messages.get(event.code):
        logger.info(message)


@create_async_listener
def handle_missed_job(event) -> None:
    """Обработчик пропущенных задач"""
    if event.code != EVENT_JOB_MISSED:
        return

    logger.info(f"⏳ Задача {event.job_id} была пропущена!")
