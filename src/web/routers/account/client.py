import json

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.schemas.service.owner import ResearchOwnerDTO
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.schemas.service.research import ResearchDTOPost, ResearchDTORel
from src.services.publisher.publisher import NatsPublisher
from src.services.research.telegram.manager import TelegramResearchManager
from src.web.dependencies.researcher.start import get_research_manager, get_publisher
from src.web.models.client import ClientConfigDTO
from src.web.models.service import ServiceClientSignupDTO

router = APIRouter(prefix="/account/client", tags=["Account"])



#TODO какие данные должна содержать модель входящих данных ? нужно ли указвать api id hash и тд

@router.post("/signup", response_model=dict, status_code=200)
async def signup_client(service_client_dto: ServiceClientSignupDTO, publisher: NatsPublisher = Depends(get_publisher)) -> dict:
    """
    Запускает новый процесс исследования.
    """
    try:
        # Создание и публикация сообщения о начале исследования
        subject_message = NatsQueueMessageDTOSubject(
            message=service_client_dto.json(),
            subject="client.telethon.create",
        )
        await publisher.publish_message_to_subject(subject_message=subject_message)
        # Возврат успешного ответа
        return {"message": f"Client '{service_client_dto.client_config.name}' started process signing up"}
    except Exception as e:
        logger.error(f"Failed to start signup process for client '{service_client_dto.client_config.name}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal registration error")