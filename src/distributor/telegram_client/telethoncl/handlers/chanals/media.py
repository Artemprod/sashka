
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
env.read_env('.env')
publisher = NatsPublisher()


@events.register(events.NewMessage(incoming=True, func=VoiceFilter(source_type=SourceType.CHANNEL)))
async def handle_voice_message_chanel(event):
    logger.info("Voice message received from CHANNEL.")


@events.register(events.NewMessage(incoming=True, func=AudioFilter(source_type=SourceType.CHANNEL)))
async def handle_audio_message_chanel(event):
    logger.info("Audio message received from CHANNEL.")


@events.register(events.NewMessage(incoming=True, func=VideoFilter(source_type=SourceType.CHANNEL)))
async def handle_video_message_chanel(event):
    logger.info("Video message received from CHANNEL.")


@events.register(events.NewMessage(incoming=True, func=PhotoFilter(source_type=SourceType.CHANNEL)))
async def handle_photo_message_chanel(event):
    logger.info("Photo message received from CHANNEL.")


@events.register(events.NewMessage(incoming=True, func=StickerFilter(source_type=SourceType.CHANNEL)))
async def handle_sticker_message_chanel(event):
    logger.info("Sticker received from CHANNEL.")


@events.register(events.NewMessage(incoming=True, func=GifFilter(source_type=SourceType.CHANNEL)))
async def handle_gif_message_chanel(event):
    logger.info("Animated GIF received from CHANNEL.")
