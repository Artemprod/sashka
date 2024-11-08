from loguru import logger
from telethon import TelegramClient
from src.distributor.app.routers.parse.gather_info import UserDTOBase
from src.distributor.exceptions.atribute import UsernameError


async def send_message(client: TelegramClient, user: UserDTOBase, body: str):
    try:
        user_entity = await client.get_input_entity(user.tg_user_id)
        return await client.send_message(entity=user_entity, message=body)
    except ValueError as e:
        logger.warning(f"Cant send vy ID Trying to send by name. {e}")
        if not user.name:
            raise UsernameError(user)
        user_entity = await client.get_input_entity(user.name)
        return await client.send_message(entity=user_entity, message=body)
    except Exception as e:
        logger.warning(f" Faild to send. {e}")
