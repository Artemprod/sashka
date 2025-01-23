from environs import Env
from loguru import logger
from telethon import events

from src.distributor.telegram_client.telethoncl.filters.media import TextFilter
from src.distributor.telegram_client.telethoncl.filters.model import SourceType
from src.services.publisher.publisher import NatsPublisher

env = Env()
env.read_env(".env")
publisher = NatsPublisher()


@events.register(events.NewMessage(incoming=True, func=TextFilter(source_type=SourceType.CHANNEL)))
async def handle_text_message_chanel(event):
    logger.info("New message from CHANNEL")
