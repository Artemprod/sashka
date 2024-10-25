import logging
import os

from environs import Env
from faststream.nats import NatsBroker
from loguru import logger
from numpy.compat import unicode
from pydantic import ValidationError
from telethon import events, TelegramClient
from telethon.tl.types import User

from src.distributor.telegram_client.telethoncl.filters.media import TextFilter, VoiceFilter, AudioFilter, \
     VideoFilter, PhotoFilter, StickerFilter, GifFilter
from src.distributor.telegram_client.telethoncl.filters.model import SourceType
from src.distributor.telegram_client.telethoncl.models.messages import OutcomeMessageDTOQueue
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.services.publisher.publisher import NatsPublisher

env = Env()
env.read_env('.env')
publisher = NatsPublisher()


@events.register(events.NewMessage(incoming=True, func=VoiceFilter(source_type=SourceType.USER)))
async def handle_voice_message_user_chat(event):
    logger.info("Voice message received USER CHAT.")


@events.register(events.NewMessage(incoming=True, func=AudioFilter(source_type=SourceType.USER)))
async def handle_audio_message_user_chat(event):
    logger.info("Audio message received USER CHAT.")




@events.register(events.NewMessage(incoming=True, func=VideoFilter(source_type=SourceType.USER)))
async def handle_video_message_user_chat(event):
    logger.info("Video message received USER CHAT.")


@events.register(events.NewMessage(incoming=True, func=PhotoFilter(source_type=SourceType.USER)))
async def handle_photo_message_user_chat(event):
    logger.info("Photo message received USER CHAT.")


@events.register(events.NewMessage(incoming=True, func=StickerFilter(source_type=SourceType.USER)))
async def handle_sticker_message_user_chat(event):
    logger.info("Sticker received USER CHAT.")


@events.register(events.NewMessage(incoming=True, func=GifFilter(source_type=SourceType.USER)))
async def handle_gif_message_user_chat(event):
    logger.info("Animated GIF received USER CHAT.")
