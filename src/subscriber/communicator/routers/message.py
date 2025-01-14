from faststream import Context
from faststream import Depends
from faststream.nats import NatsMessage
from faststream.nats import NatsRouter

from configs.nats_queues import nats_subscriber_communicator_settings
from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.services.communicator.communicator import TelegramCommunicator
from src.subscriber.communicator.dependency.message import get_data_from_headers as message_former
from src.subscriber.communicator.utils.message_handler import handle_incoming_message
from src.subscriber.communicator.utils.message_handler import process_voice_message

router = NatsRouter()


@router.subscriber(subject=nats_subscriber_communicator_settings.messages.new_text_message)
async def new_text_message_handler(
        body: str,
        msg: NatsMessage,
        context=Context(),
        income_message_data: IncomeUserMessageDTOQueue = Depends(message_former)
):
    """
    Обрабатывает воходящие текстовые сообщения
    """
    communicator: TelegramCommunicator = context.get("communicator")
    await handle_incoming_message(income_message_data, communicator)


@router.subscriber(subject=nats_subscriber_communicator_settings.messages.new_voice_message)
async def new_audio_message_handler(
        body: str,
        msg: NatsMessage,
        context=Context(),
        income_message_data: IncomeUserMessageDTOQueue = Depends(message_former)
):
    """Обрабатывает новые входящие аудио сообщения."""
    communicator: TelegramCommunicator = context.get("communicator")
    await process_voice_message(income_message_data, communicator)
    await handle_incoming_message(income_message_data, communicator)
