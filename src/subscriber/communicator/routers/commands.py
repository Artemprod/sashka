from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsMessage
from loguru import logger

from src.schemas.communicator.message import IncomeUserMessageDTOQueue
from src.services.communicator.communicator import TelegramCommunicator
from src.subscriber.communicator.dependency.message import get_data_from_headers as message_former

router = NatsRouter()

# Подписчик на новую входящую тему
# @router.subscriber(subject="command.ferst_message.distribute")
# async def new_message_handler(
#         body: str,
#         msg: NatsMessage,
#         context=Context(),
#         # income_message_data: IncomeUserMessageDTOQueue = Depends(message_former)
# ):
#     """Обрабатывает новые входящие сообщения."""
#     # Получение экземпляра TelegramCommunicator из контекста
#     communicator: TelegramCommunicator = context.get("communicator")
#     try:
#         # Обработка сообщения с использованием TelegramCommunicator
#         await communicator.make_first_message_distribution(research_id, users])
#         logger.info("reply to message ")
#     except Exception as e:
#         logger.error("Failed to reply ")
#         raise e
