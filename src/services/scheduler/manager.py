#______ Паттерн
import contextlib
import inspect
from typing import Optional, Callable, List, Union

import pytz
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_SCHEDULER_STARTED, EVENT_SCHEDULER_SHUTDOWN, \
    EVENT_JOB_MISSED
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler
from loguru import logger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from pydantic import BaseModel

from configs.database import database_postgres_settings
from configs.redis import redis_apscheduler_config

from abc import ABC, abstractmethod

from src.services.scheduler.event_handlers import handle_scheduler_event, handle_job_event, handle_missed_job
from src.utils.wrappers import async_wrap

from src.services.scheduler import event_handlers



class IAsyncSchedularManager(ABC):pass


class BaseAsyncSchedularManager:

    def __init__(self):
        self._event_handlers = None
        self._schedular: Optional[AsyncIOScheduler] = None
        self._event_handlers:list[Callable] =[]

    # Получает экземпляр с настройками
    @property
    def schedular(self) -> AsyncIOScheduler:
        if self._schedular is None:
            self._init_schedular()
        return self._schedular

    def _init_schedular(self):
        raise NotImplemented

    @property
    def event_handlers(self):
        return self._event_handlers.copy()

    def set_event_handlers(self, handlers: Union[Callable, List[Callable]]) -> None:
        """
        Полностью заменяет список обработчиков.

        :param handlers: Либо одиночный обработчик, либо список обработчиков.
        :raises ValueError: Если аргумент не является вызываемым объектом или списком вызываемых объектов.
        """
        if isinstance(handlers, list):
            if not all(callable(handler) for handler in handlers):
                raise ValueError("Все элементы списка должны быть вызываемыми (callable).")
            self._event_handlers = handlers.copy()
        elif callable(handlers):
            self._event_handlers = [handlers]
        else:
            raise ValueError("Аргумент должен быть вызываемым объектом или списком вызываемых объектов.")

    def add_event_handler(self, handler: Union[Callable, List[Callable]]) -> None:
        """
        Добавляет один или несколько обработчиков к существующему списку.

        :param handler: Либо одиночный обработчик, либо список обработчиков.
        :raises ValueError: Если аргумент не является вызываемым объектом или списком вызываемых объектов.
        """
        if isinstance(handler, list):
            if not all(callable(h) for h in handler):
                raise ValueError("Все элементы списка должны быть вызываемыми (callable).")
            self._event_handlers.extend(handler)
        elif callable(handler):
            self._event_handlers.append(handler)
        else:
            raise ValueError("Аргумент должен быть вызываемым объектом или списком вызываемых объектов.")

    def start(self) -> None:
        """Запуск планировщика"""
        self._init_schedular()
        self._schedular.start()
        logger.debug("Schedular has been started")

    def shutdown(self) -> None:
        """Остановка планировщика"""
        self._schedular.shutdown()

    def _setup_handlers(self) -> None:
        """Настройка слушателей событий"""
        if not self._event_handlers:
            return
        for handler in self._event_handlers:
            self._schedular.add_listener(handler)

    @async_wrap
    def delete_scheduled_task(
            self,
            prefix: str
    ) -> int:
        """
        Removes scheduled tasks based on the job id prefix.

        :param prefix: Prefix to identify the task.
        :return: Number of removed jobs.
        """
        removed_jobs_count = 0
        for job in self._schedular.get_jobs():
            if job.id.startswith(prefix):
                logger.info(f"Job ID: {job.id}")
                self._schedular.remove_job(job.id)
                logger.info(f"Removed job: {job.id}")
                removed_jobs_count += 1
        return removed_jobs_count



#TODO задание настроек
class AsyncPostgresSchedularManager(BaseAsyncSchedularManager):

    """
    Хранит id задач
    может отменять
    ставить на паузу

    """

    def __init__(self):
        super().__init__()
        self._schedular:Optional[AsyncIOScheduler] = None




    def replace_driver(self, link: str) -> str:
        import re
        # Если ссылка уже содержит postgresql+psycopg2, возвращаем её без изменений
        if "postgresql+psycopg2" in link:
            return link

        # Если найден точный совпадение postgresql+asyncpg, то заменяем его
        pattern = r"postgresql\+asyncpg"
        replacement = "postgresql+psycopg2"
        new_link = re.sub(pattern, replacement, link)
        return new_link

    def _init_schedular(self):
        from sqlalchemy import create_engine

        # Производим замену драфвера если требуется
        url = self.replace_driver(database_postgres_settings.sync_postgres_url)
        logger.info(f"postgres url {url}")
        engine = create_engine(url)

        jobstores = {
            'default': SQLAlchemyJobStore(url=url,engine=engine),

        }
        # Исполнители определяют, как именно задачи выполняются.
        executors = {
            'default': AsyncIOExecutor(),  # По дефолту в асинхронном контексте ( в лупе ) запускает задачи

        }
        # настройки применяются к каждой задаче, если они не были заданы вручную.
        job_defaults = {
            'coalesce': False,  # (True/False) – если True, то пропущенные задачи объединяются в одну,
            # если False, выполняются все пропущенные.
            'max_instances': 1,
            # (int) – максимальное число одновременных запусков одной и той же задачи. Предотвращает дубли
            'misfire_grace_time': 60 * 2,
            # (int) – время (в секундах), в течение которого можно выполнить задачу после пропуска.
            'replace_existing ': True,  # (True/False) – если True, то новая задача заменяет существующую с таким же ID.

        }

        self._schedular = AsyncIOScheduler(

            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.utc
        )
        self._setup_handlers()
        return self._schedular



class AsyncRedisApschedulerManager(BaseAsyncSchedularManager):
    def __init__(self):
        super().__init__()
        self._schedular: Optional[AsyncIOScheduler] = None

    def _init_schedular(self):

        jobstores = {
            "default": RedisJobStore(
                jobs_key=redis_apscheduler_config.jobs_key,  # Ключ для хранения заданий
                run_times_key=redis_apscheduler_config.run_times_key,  # Ключ для времени выполнения
                host=redis_apscheduler_config.host,
                port=redis_apscheduler_config.port,
                db=redis_apscheduler_config.research_start_database,
            )
        }
        # Исполнители определяют, как именно задачи выполняются.
        executors = {
            'default': AsyncIOExecutor(),  # По дефолту в асинхронном контексте ( в лупе ) запускает задачи


        }
        # настройки применяются к каждой задаче, если они не были заданы вручную.
        job_defaults = {
            'coalesce': False,  # (True/False) – если True, то пропущенные задачи объединяются в одну,
            # если False, выполняются все пропущенные.
            'max_instances': 1,
            # (int) – максимальное число одновременных запусков одной и той же задачи. Предотвращает дубли
            'misfire_grace_time': 60 * 2,
            # (int) – время (в секундах), в течение которого можно выполнить задачу после пропуска.
            'replace_existing ': True,  # (True/False) – если True, то новая задача заменяет существующую с таким же ID.

        }

        self._schedular = AsyncIOScheduler(

            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.utc
        )
        self._setup_handlers()
        return self._schedular


    def get_scheduler(self) -> AsyncIOScheduler:
        return self._schedular



