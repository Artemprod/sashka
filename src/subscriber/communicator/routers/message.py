from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsMessage
from loguru import logger

from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.services.communicator.communicator import TelegramCommunicator
from src.subscriber.communicator.dependency.message import get_data_from_headers as message_former

router = NatsRouter()

# Подписчик на новую входящую тему
@router.subscriber(subject="message.income.new")
async def new_message_handler(
        body: str,
        msg: NatsMessage,
        context=Context(),
        income_message_data: IncomeUserMessageDTOQueue = Depends(message_former)
):
    """Обрабатывает новые входящие сообщения."""
    # Получение экземпляра TelegramCommunicator из контекста
    communicator: TelegramCommunicator = context.get("communicator")
    logger.info(f"ЭТО СФОРМИРОВАННОЕ СООБЩЕНИЕ{income_message_data}")
    try:
        # Обработка сообщения с использованием TelegramCommunicator
        await communicator.reply_message(message_object=income_message_data)
        logger.info("reply to message ")
    except Exception as e:
        logger.error("Failed to reply ")
        raise e
