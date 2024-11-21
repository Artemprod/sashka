from loguru import logger
from telethon import TelegramClient

from src.distributor.app.schemas.message import UserDTOBase
from src.distributor.exceptions.atribute import UsernameError


async def send_message(client: TelegramClient, user: UserDTOBase, message: str):
    try:
        user_entity = await client.get_input_entity(user.tg_user_id)
        return await client.send_message(entity=user_entity, message=message)
    except ValueError as e:
        logger.warning(f"Cant send vy ID Trying to send by name. {e}")
        if not user.name:
            logger.warning(f"No username {e}")
        user_entity = await client.get_input_entity(user.name)
        return await client.send_message(entity=user_entity, message=message)
    except Exception as e:
        logger.warning(f" Faild to send. {e}")
