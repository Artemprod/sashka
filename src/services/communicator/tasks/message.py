from dataclasses import dataclass
from typing import Callable, Optional
from datetime import datetime
import asyncio
from functools import wraps

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import (
    EVENT_SCHEDULER_STARTED,
    EVENT_SCHEDULER_SHUTDOWN,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED
)
from apscheduler.triggers.date import DateTrigger
from loguru import logger

from src.database.postgres.engine.session import DatabaseSessionManager
from src.database.repository.storage import RepoStorage
from src.services.communicator.messager import MessageFirstSend
from src.services.communicator.prompt_generator import ExtendedPingPromptGenerator
from src.services.communicator.request import SingleRequest
from src.services.publisher.publisher import NatsPublisher
from src.schemas.service.user import UserDTOBase
from configs.database import database_postgres_settings
from configs.ai_api_endpoints import open_ai_api_endpoint_settings
from src.services.scheduler.event_handlers import handle_scheduler_event, handle_job_event, handle_missed_job
from src.services.scheduler.manager import AsyncPostgresSchedularManager, AsyncPostgresSetting


class MessageService:
    """Класс для управления сервисами сообщений"""

    def __init__(self):
        self.database_session_manager = DatabaseSessionManager(
            database_url=database_postgres_settings.async_postgres_url
        )
        self.repository = RepoStorage(database_session_manager=self.database_session_manager)
        self.publisher = NatsPublisher()
        self.single_request = SingleRequest(url=open_ai_api_endpoint_settings.single_response_url)
        self.prompt_generator = ExtendedPingPromptGenerator(repository=self.repository)

    def create_first_message_sender(self) -> MessageFirstSend:
        """Создает экземпляр отправителя сообщений"""
        return MessageFirstSend(
            publisher=self.publisher,
            repository=self.repository,
            single_request=self.single_request,
            prompt_generator=self.prompt_generator
        )


async def plan_first_message(
        user: UserDTOBase,
        send_time: datetime,
        research_id: int,
        client: "TelegramClientDTOGet",
        assistant_id: int,
        destination_configs: "NatsDestinationDTO",
) -> None:
    """Планирование первого сообщения"""
    message_sender = MessageService().create_first_message_sender()
    await message_sender._process_user(
        user, send_time, research_id, client, assistant_id, destination_configs
    )



if __name__ == '__main__':
    async def main():
        scheduler_manager = AsyncPostgresSchedularManager(AsyncPostgresSetting(
            DATABASE_URL=database_postgres_settings.async_postgres_url,
            TABLE_NAME="apscheduler_communicator",
        ))

        scheduler_manager.add_event_handler(handle_scheduler_event)
        scheduler_manager.add_event_handler(handle_job_event)
        scheduler_manager.add_event_handler(handle_missed_job)
        scheduler_manager.start()


        scheduler_manager.schedular.add_job(
                        func=plan_first_message,
                                            args=[1, 2, 3, 3, 4, 4],
                                                 trigger=DateTrigger(run_date=datetime.now(),
                                                                     timezone=pytz.utc),
                    id=f"first_message:research:{0}:user:{2}:{int(datetime.now().timestamp())}",
                    name=f"first_message_generation:{21}:{2}")

        scheduler_manager.shutdown()



    asyncio.run(main())