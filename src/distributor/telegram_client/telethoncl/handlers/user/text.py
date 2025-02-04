from typing import Optional

from loguru import logger
from telethon import events

from configs.nats_queues import nats_subscriber_communicator_settings
from src.distributor.telegram_client.telethoncl.filters.media import TextFilter
from src.distributor.telegram_client.telethoncl.filters.model import SourceType
from src.distributor.telegram_client.telethoncl.handlers.base_handler import base_message_handler


@events.register(
    events.NewMessage(
        incoming=True,
        func=TextFilter(source_type=SourceType.USER)
    )
)
@base_message_handler(nats_subscriber_communicator_settings.messages.new_text_message)
async def handle_text_message_user_chat(event) -> Optional[str]:
    logger.info("New message from USER CHAT")
    return
