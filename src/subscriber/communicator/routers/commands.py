from faststream import Context, Depends
from faststream.nats import NatsRouter, NatsMessage
from loguru import logger


from src.services.communicator.communicator import TelegramCommunicator
from src.subscriber.communicator.dependency.command import get_command_ping_user, \
    get_command_start_dialog_data_from_headers
from src.subscriber.communicator.dependency.message import get_data_from_headers as message_former
from src.subscriber.communicator.schemas.command import CommandPingUserDTO

router = NatsRouter()


@router.subscriber(subject="command.dialog.start")
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
        await communicator.make_first_message_distribution(command_data.research_id, command_data.users)
        logger.info("reply to message ")
    except Exception as e:
        logger.error("Failed to send first message ")
        raise e


@router.subscriber(subject="command.user.ping")
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
