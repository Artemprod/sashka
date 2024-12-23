import asyncio

from faststream import Context
from faststream import Depends
from faststream.nats import NatsMessage
from faststream.nats import NatsRouter
from loguru import logger

from configs.nats_queues import nats_subscriber_communicator_settings
from src.services.communicator.communicator import TelegramCommunicator
from src.subscriber.communicator.dependency.command import get_command_ping_user
from src.subscriber.communicator.dependency.command import get_command_start_dialog_data_from_headers
from src.subscriber.communicator.schemas.command import CommandPingUserDTO

router = NatsRouter()


@router.subscriber(subject=nats_subscriber_communicator_settings.commands.start_dialog)
async def command_dialog_start(
        body: str,
        msg: NatsMessage,
        context=Context(),
        command_data=Depends(get_command_start_dialog_data_from_headers)
):
    """Обрабатывает новые входящие сообщения."""
    # Получение экземпляра TelegramCommunicator из контекста
    communicator: TelegramCommunicator = context.get("communicator")
    try:
        # Обработка сообщения с использованием TelegramCommunicator
        task = asyncio.create_task(communicator.make_first_message_distribution(command_data.research_id, command_data.users))
        logger.debug("ВЫЗВАЛАСЬ ТАСКА С ОЗДАНИЕМ ИСЛЕДОВНИЯ  ")
        logger.info("reply to message ")
    except Exception as e:
        logger.error("Failed to send first message ")
        raise e


@router.subscriber(subject=nats_subscriber_communicator_settings.commands.ping_user)
async def command_user_ping(
        body: str,
        msg: NatsMessage,
        context=Context(),
        command_ping_data: CommandPingUserDTO = Depends(get_command_ping_user)
):
    """Обрабатывает новые входящие сообщения."""
    # Получение экземпляра TelegramCommunicator из контекста
    communicator: TelegramCommunicator = context.get("communicator")
    try:
        # Обработка сообщения с использованием TelegramCommunicator
        await communicator.ping_user(user=command_ping_data.user,
                                     message_number=command_ping_data.message_number,
                                     research_id=command_ping_data.research_id)
        logger.info("user has been pinged  ")
    except Exception as e:
        logger.error("Failed to ping  ")
        raise e
