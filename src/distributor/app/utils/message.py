from faststream.nats import NatsMessage
from loguru import logger
from telethon import TelegramClient

from src.distributor.app.schemas.message import MessageContext
from src.distributor.app.schemas.message import MessageToSendData
from src.distributor.app.schemas.message import UserDTOBase


async def process_message(
        data: MessageToSendData,
        msg: NatsMessage,
        context: MessageContext,
        is_first_message: bool = False
) -> bool:
    await msg.ack()
    logger.info("Sending message...")

    if not data.message:
        logger.warning("There is no message to send, I will not send anything")
        return False

    if is_first_message and await context.client_ban_checker.check_is_account_banned(client=context.client):
        await context.client_ban_checker.start_check_ban(
            client=context.client,
            research_id=context.research_id
        )
        return False

    msg_data = await send_message(
        client=context.client,
        user=data.user,
        message=data.message
    )
    logger.info(f"Message sent: {msg_data}")
    return True


async def send_message(client: TelegramClient, user: UserDTOBase, message: str):
    try:
        user_entity = await client.get_input_entity(user.tg_user_id)
        return await client.send_message(
            entity=user_entity,
            message=message
        )

    except ValueError as e:
        logger.warning(f"Cant send vy ID Trying to send by name. {e}")
        if not user.name:
            logger.warning(f"No username {e}")
        user_entity = await client.get_input_entity(user.name)
        return await client.send_message(
            entity=user_entity,
            message=message
        )
    except Exception as e:
        logger.warning(f" Faild to send. {e}")
