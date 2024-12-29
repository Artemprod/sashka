from environs import Env
from loguru import logger
from telethon import events

from src.distributor.telegram_client.telethoncl.filters.media import AudioFilter
from src.distributor.telegram_client.telethoncl.filters.media import GifFilter
from src.distributor.telegram_client.telethoncl.filters.media import PhotoFilter
from src.distributor.telegram_client.telethoncl.filters.media import StickerFilter
from src.distributor.telegram_client.telethoncl.filters.media import VideoFilter
from src.distributor.telegram_client.telethoncl.filters.media import VoiceFilter
from src.distributor.telegram_client.telethoncl.filters.model import SourceType
from src.services.publisher.publisher import NatsPublisher

env = Env()
env.read_env(".env")
publisher = NatsPublisher()


@events.register(events.NewMessage(incoming=True, func=VoiceFilter(source_type=SourceType.PRIVATE_CHAT)))
async def handle_voice_message(event):
    logger.info("Voice received from PRIVATE CHAT ")


@events.register(events.NewMessage(incoming=True, func=AudioFilter(source_type=SourceType.PRIVATE_CHAT)))
async def handle_audio_message_private_chat(event):
    logger.info("Audio message received from PRIVATE CHAT.")


@events.register(events.NewMessage(incoming=True, func=VideoFilter(source_type=SourceType.PRIVATE_CHAT)))
async def handle_video_message_private_chat(event):
    logger.info("Video message received from PRIVATE CHAT.")


@events.register(events.NewMessage(incoming=True, func=PhotoFilter(source_type=SourceType.PRIVATE_CHAT)))
async def handle_photo_message_private_chat(event):
    logger.info("Photo message received from PRIVATE CHAT.")


@events.register(events.NewMessage(incoming=True, func=StickerFilter(source_type=SourceType.PRIVATE_CHAT)))
async def handle_sticker_message_private_chat(event):
    logger.info("Sticker received from PRIVATE CHAT.")


@events.register(events.NewMessage(incoming=True, func=GifFilter(source_type=SourceType.PRIVATE_CHAT)))
async def handle_gif_message_private_chat(event):
    logger.info("Animated GIF received from PRIVATE CHAT.")
