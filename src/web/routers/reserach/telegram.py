import json

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from configs.nats import nats_subscriber_researcher_settings
from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.schemas.service.research import ResearchDTOPost, ResearchDTORel
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager
from src.web.dependencies.researcher.start import get_research_manager, get_publisher

router = APIRouter(prefix="/research/telegram", tags=["Research"])


# TODO входящий контракт должен сожержать в себе все данные овнер ресерч какой клиент ( бота которого выбрали )

@router.post("/start", response_model=dict, status_code=200)
async def start_research(
        research: ResearchDTOPost,
        owner: ResearchOwnerDTO,
        manager: TelegramResearchManager = Depends(get_research_manager),
        publisher: NatsPublisher = Depends(get_publisher)
) -> dict:
    """Запускает новый процесс исследования."""
    try:
        # Создание нового исследования
        created_research: ResearchDTORel = await manager.create_research(research=research, owner=owner)

        # Создание и публикация сообщения о начале исследования
        subject_message = NatsQueueMessageDTOSubject(
            message='',
            subject=nats_subscriber_researcher_settings.researches.start_telegram_research,
            headers={"research_id": str(created_research.research_id)}
        )
        await publisher.publish_message_to_subject(subject_message=subject_message)

        return {
            "message": f"Research '{created_research.name}' has been started",
            "research_id": created_research.research_id
        }
    except Exception as e:
        logger.error(f"Failed to start research: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")
