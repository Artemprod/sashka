from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from loguru import logger

from configs.nats_queues import nats_subscriber_researcher_settings
from src.schemas.information.start_research import UserInfo
from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.schemas.service.research import ResearchDTOPost
from src.schemas.service.research import ResearchDTORel
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager
from src.web.dependencies.researcher.start import get_publisher, get_apscheduler
from src.web.dependencies.researcher.start import get_research_manager
from src.web.dependencies.researcher.validation import validate_data
from src.web.utils.funcs import count_users_in_research

router = APIRouter(prefix="/research/telegram", tags=["Research"])


# TODO входящий контракт должен сожержать в себе все данные овнер ресерч какой клиент ( бота которого выбрали )

@router.post("/start", response_model=dict, status_code=200)
async def start_research(
        research: ResearchDTOPost,
        owner: ResearchOwnerDTO,
        manager: TelegramResearchManager = Depends(get_research_manager),
        publisher: NatsPublisher = Depends(get_publisher),
        apscheduler: AsyncIOScheduler = Depends(get_apscheduler)
) -> dict:
    """Запускает новый процесс исследования."""


    try:
        validated_research = await validate_data(research)
        # Создание нового исследования
        created_research: ResearchDTORel = await manager.create_research(research=validated_research, owner=owner)
        # Создание и публикация сообщения о начале исследования
        subject_message = NatsQueueMessageDTOSubject(
            message='',
            subject=nats_subscriber_researcher_settings.researches.start_telegram_research,
            headers={"research_id": str(created_research.research_id)}
        )

        #FIXME Тут скорее вынести в сервис начала иследования разделение ответсвенности представление не должно знать бизнес логику
        # Запланировать публикацию сообщения через 5 минут после начала исследования
        apscheduler.add_job(
            publisher.publish_message_to_subject,
            args=[subject_message],
            trigger=DateTrigger(run_date=created_research.start_date, timezone=pytz.utc)
        )
        user_info:UserInfo = await count_users_in_research(users_dto=created_research.users,research=research)

        #TODO переписать в модель DTO
        return {
            "message": f"Research '{created_research.name}' has been planed to start at {created_research.start_date}",
            "research_id": created_research.research_id,
            "users_info":user_info.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start research: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}") from e


#Для отмены запланированой задачи
# @app.route("/")
# async def add_task():
#     """Добавляем задачу в планировщик"""
#     scheduler.add_job(my_scheduled_task, "interval", seconds=5, id="example_task")
#     return "Task added!"
#
# @app.route("/remove-task")
# async def remove_task():
#     """Удаляем задачу из планировщика"""
#     scheduler.remove_job("example_task")
#     и тут аборт джобы
#     return "Task removed!"