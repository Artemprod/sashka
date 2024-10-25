import json
import logging
import os

from environs import Env
from faststream.nats import NatsBroker
from loguru import logger
from numpy.compat import unicode
from pydantic import ValidationError
from telethon import events, TelegramClient
from telethon.tl.types import  User


from src.distributor.telegram_client.telethoncl.filters.media import TextFilter
from src.distributor.telegram_client.telethoncl.filters.model import SourceType
from src.distributor.telegram_client.telethoncl.models.messages import OutcomeMessageDTOQueue
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.services.publisher.publisher import NatsPublisher

env = Env()
env.read_env('.env')
publisher = NatsPublisher()


@events.register(events.NewMessage(incoming=True, func=TextFilter(source_type=SourceType.CHANNEL)))
async def handle_text_message_chanel(event):
    logger.info(f"New message from CHANNEL")

