import logging
import os

from loguru import logger
from telethon import events, types, functions


@events.register(events.NewMessage(incoming=True))
async def handle_voice_message(event):
    logger.info(f"New message")