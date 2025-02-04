import asyncio

from faststream import Context
from faststream import Depends
from faststream.nats import JStream
from faststream.nats import NatsMessage
from faststream.nats import NatsRouter
from loguru import logger
from nats.js.api import DeliverPolicy
from nats.js.api import RetentionPolicy

from configs.nats_queues import nats_distributor_settings
from src.database.postgres import UserStatusEnum
from src.database.repository.storage import RepoStorage
from src.distributor.app.dependency.message import get_data_from_body, get_research_id, get_telegram_client_name
from src.distributor.app.dependency.message import get_telegram_client
from src.distributor.app.utils.message import process_message
from src.distributor.app.schemas.message import MessageContext

# Создаем маршрутизатор NATS и две очереди JStream
router = NatsRouter()


@router.subscriber(
    stream=JStream(
        name=nats_distributor_settings.message.first_message_message.stream,
        retention=RetentionPolicy.WORK_QUEUE
    ),
    subject=nats_distributor_settings.message.first_message_message.subject,
    deliver_policy=DeliverPolicy.ALL,
    no_ack=True,
)
async def send_first_message_subscriber(
    body: str,
    msg: NatsMessage,
    context=Context(),
    data=Depends(get_data_from_body),
    client=Depends(get_telegram_client),
    client_name=Depends(get_telegram_client_name),
    research_id=Depends(get_research_id),
):
    print()
    message_context = MessageContext(
        client=client,
        publisher=context.get("publisher"),
        client_ban_checker=context.get("client_ban_checker"),
        research_id=research_id,
        client_name=client_name
    )

    if not await process_message(
        data=data,
        msg=msg,
        context=message_context,
        is_first_message=True
    ):
        return

    repository: RepoStorage = context.get("repository")
    await repository.user_in_research_repo.short.update_user_status(
        telegram_id=data.user.tg_user_id,
        status=UserStatusEnum.IN_PROGRESS
    )

@router.subscriber(
    stream=JStream(
        name=nats_distributor_settings.message.send_message.stream,
        retention=RetentionPolicy.WORK_QUEUE
    ),
    subject=nats_distributor_settings.message.send_message.subject,
    deliver_policy=DeliverPolicy.ALL,
    no_ack=True,
)
async def send_message_subscriber(
        body: str,
        msg: NatsMessage,
        context=Context(),
        data=Depends(get_data_from_body),
        client=Depends(get_telegram_client),
):
    """Send a conversation message."""
    message_id = getattr(data, 'message_id', 'unknown')
    logger.info(f"Message {message_id} acknowledged")

    message_context = MessageContext(
        client=client,
        publisher=context.get("publisher"),
        research_id=None,
        client_name=None
    )

    # Создаем задачу отправки сообщения на фоне
    asyncio.create_task(
        await process_message(
            data=data,
            msg=msg,
            context=message_context,
            is_first_message=False
        ),
        name=f"send_message_{message_id}"
    )

    logger.info(f"Created send task for message {message_id}")


