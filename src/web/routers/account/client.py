from typing import List, Dict

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from loguru import logger

from configs.nats_queues import nats_distributor_settings
from src.database.exceptions.read import EmptyTableError, NoFreeClientsError
from src.database.repository.storage import RepoStorage
from src.schemas.service.client import TelegramClientDTOGet, TelegramClientDTOResponse
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.services.publisher.publisher import NatsPublisher
from src.web.dependencies.researcher.start import get_publisher, get_repository
from src.web.models.service import ServiceClientSignupDTO

router = APIRouter(prefix="/account/client", tags=["Account"])


# TODO какие данные должна содержать модель входящих данных ? нужно ли указвать api id hash и тд


@router.post("/signup", response_model=dict, status_code=200)
async def signup_client(
    service_client_dto: ServiceClientSignupDTO, publisher: NatsPublisher = Depends(get_publisher)
) -> dict:
    """
    Запускает новый процесс исследования.
    """
    try:
        # Создание и публикация сообщения о начале исследования
        subject_message = NatsQueueMessageDTOSubject(
            message=service_client_dto.json(),
            subject=nats_distributor_settings.client.create_new_client,
        )
        await publisher.publish_message_to_subject(subject_message=subject_message)
        # Возврат успешного ответа
        return {"message": f"Client '{service_client_dto.client_config.name}' started process signing up"}
    except Exception as e:
        logger.error(f"Failed to start signup process for client '{service_client_dto.client_config.name}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal registration error")


@router.get("/get/readyforwork", response_model=Dict[str, TelegramClientDTOResponse], status_code=200)
async def get_ready_for_work_clients(
    repository: RepoStorage = Depends(get_repository),
) -> Dict[str, TelegramClientDTOResponse]:
    """Выдает всех работающих клиентов"""
    try:
        clients: List[TelegramClientDTOGet] = await repository.client_repo.get_clients_ready_for_research()
        return {client.name: TelegramClientDTOResponse(**client.dict()) for client in clients}
    except NoFreeClientsError:
        raise HTTPException(status_code=404, detail="No working clients found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
