import asyncio
from typing import Union, Optional

from faststream.nats import NatsMessage
from loguru import logger
from telethon import TelegramClient, types, functions
from telethon.errors.rpcerrorlist import ChatWriteForbiddenError
from telethon.errors.rpcerrorlist import PeerFloodError
from telethon.errors.rpcerrorlist import UserDeactivatedBanError

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

    if not data.message or not data.message:
        logger.warning("There is no message to send,, skipping")
        return False

    if is_first_message and await context.client_ban_checker.check_is_account_banned(client=context.client):
        await context.client_ban_checker.start_check_ban(
            client=context.client,
            research_id=context.research_id
        )
        return False
    try:

        msg_data = await send_message(
            client=context.client,
            user=data.user,
            message=data.message,
            context=context
        )


        if isinstance(msg_data, types.Message):
            logger.info(
                f"Message {message_id} sent successfully to user {data.user.tg_user_id}. "
                f"Telegram message ID: {msg_data.id}"
            )
        else:
            logger.warning(
                f"Message {message_id} sent, but returned unexpected result type: {type(msg_data)}"
            )

        if msg_data is None:
            logger.warning("Error in sending message")
            return False

        logger.info(f"Message sent: {msg_data}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send message {message_id}: {str(e)}",
            extra={
                "user_id": getattr(data, 'user', {}).get('tg_user_id', 'unknown'),
                "message_id": message_id
            }
        )


async def send_message(
        client: TelegramClient,
        user: UserDTOBase,
        message: str,
        context: MessageContext,
        read_message_delay: float = 4.0,
        typing_delay: float = 7.0,

):

    try:

        # Пробуем получить сущность по ID или имени
        user_entity = await client.get_input_entity(user.name)

        await client(functions.messages.ReadHistoryRequest(
            peer=user_entity,
            max_id=0
        ))

        # Добавляем задержку для эффекта чтения
        await asyncio.sleep(read_message_delay)
        # Устанавливаем статус "печатает"
        await client(functions.messages.SetTypingRequest(
            peer=user_entity,
            action=types.SendMessageTypingAction()
        ))

        # Добавляем задержку для эффекта печатания
        await asyncio.sleep(typing_delay)

        return await client.send_message(
            entity=user_entity,
            message=message
        )

    except (UserDeactivatedBanError, ChatWriteForbiddenError, PeerFloodError) as e:
        logger.error(f"Аккаунт, скорее всего, заблокирован! Ошибка: {e} ")
        if await context.client_ban_checker.check_is_account_banned(client=context.client):
            logger.info(f"Проверил через бан чекера. Клиент {context.client} имеет бан.")
            await context.client_ban_checker.start_check_ban(
                client=context.client,
                research_id=context.research_id
            )
            return
        logger.warning(f"Проверил через бан чекера. Клиент {context.client} не имеет бан. ")


    except ValueError as e:
        logger.warning(f"Cant send vy ID Trying to send by name. {e}")
        if not user.name:
            logger.warning(f"No username {e}")

        user_entity = await client.get_input_entity(user.tg_user_id)

        await client(functions.messages.ReadHistoryRequest(
            peer=user_entity,
            max_id=0
        ))
        # Добавляем задержку для эффекта чтения
        await asyncio.sleep(read_message_delay)

        # Устанавливаем статус "печатает"
        await client(functions.messages.SetTypingRequest(
            peer=user_entity,
            action=types.SendMessageTypingAction()
        ))

        # Добавляем задержку для эффекта печатания
        await asyncio.sleep(typing_delay)

        return await client.send_message(
            entity=user_entity,
            message=message
        )


    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        return None