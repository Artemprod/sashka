import asyncio
from typing import Union, Optional


from loguru import logger
from telethon import TelegramClient, types, functions

from faststream.nats import NatsMessage
from loguru import logger
from telethon import TelegramClient, types, functions
from telethon.errors.rpcerrorlist import ChatWriteForbiddenError
from telethon.errors.rpcerrorlist import PeerFloodError
from telethon.errors.rpcerrorlist import UserDeactivatedBanError


from src.distributor.app.schemas.message import MessageContext
from src.distributor.app.schemas.message import MessageToSendData
from src.distributor.app.schemas.message import UserDTOBase
from src.services.exceptions.telegram_clients import AllClientsBannedError


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

    try:
        # Проверка на бан клиента
        if is_first_message and await context.client_ban_checker.check_is_account_banned(client=context.client):
            # Если клиент забанен то заводим задачу на чек бана ( функция возвращает None )
            await context.client_ban_checker.start_check_ban(
                client=context.client,
                research_id=context.research_id
            )
            # Берем свободного не забаненного клиента который указан в ресерче
            context.client = await context.telethon_container.get_telethon_client_by_research_id(
                research_id=context.research_id
            )

        # Просто сделал явную проверку на True
        if is_first_message is True:
            logger.debug("First message")
            msg_data = await send_first_message(
                user=data.user,
                message=data.message,
                context=context)

        else:
            logger.debug("Usual message")
            msg_data = await send_message(
                user=data.user,
                message=data.message,
                context=context
            )


        if isinstance(msg_data, types.Message):
            logger.info(
                f"Message sent successfully to user {data.user.tg_user_id}. "
                f"Telegram message ID: {msg_data.id}"
            )
        else:
            logger.warning(
                f"Message sent, but returned unexpected result type: {type(msg_data)}"
            )

        if msg_data is None:
            logger.warning("Error in sending message")
            return False

        logger.info(f"Message sent: {msg_data}")
        return True

    except AllClientsBannedError:
        logger.warning(f"All clients banned for research_id: {context.research_id}. Publishing ban on research.")
        await context.client_ban_checker.publisher.publish_ban_on_research(
            research_id=context.research_id
        )
        return False

    except Exception as e:
        logger.error(
            f"Failed to send message: {str(e)}",
            extra={
                "user_id": getattr(data, 'user', {}).get('tg_user_id', 'unknown'),
            }
        )

async def send_first_message(
        user: UserDTOBase,
        message: str,
        context: MessageContext
):
    try:
        user_entity = await context.client.get_input_entity(user.tg_user_id)
        return await context.client.send_message(
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
        user_entity = await context.client.get_input_entity(user.name)
        return await context.client.send_message(
            entity=user_entity,
            message=message
        )
    except Exception as e:
        logger.warning(f" Faild to send. {e}")


async def send_message(
        user: UserDTOBase,
        message: str,
        context: MessageContext,
        read_message_delay: float = 5.0,
        typing_delay: float = 7.0,

):

    try:

        # Пробуем получить сущность по ID или имени
        user_entity = await context.client.get_input_entity(user.tg_user_id)
        # user_entity = await context.client.get_input_entity(user.name)

        await context.client(functions.messages.ReadHistoryRequest(
            peer=user_entity,
            max_id=0
        ))

        # Добавляем задержку для эффекта чтения
        await asyncio.sleep(read_message_delay)
        # Устанавливаем статус "печатает"
        await context.client(functions.messages.SetTypingRequest(
            peer=user_entity,
            action=types.SendMessageTypingAction()
        ))

        # Добавляем задержку для эффекта печатания
        await asyncio.sleep(typing_delay)

        return await context.client.send_message(
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

        user_entity = await context.client.get_input_entity(user.tg_user_id)

        await context.client(functions.messages.ReadHistoryRequest(
            peer=user_entity,
            max_id=0
        ))
        # Добавляем задержку для эффекта чтения
        await asyncio.sleep(read_message_delay)

        # Устанавливаем статус "печатает"
        await context.client(functions.messages.SetTypingRequest(
            peer=user_entity,
            action=types.SendMessageTypingAction()
        ))

        # Добавляем задержку для эффекта печатания
        await asyncio.sleep(typing_delay)

        return await context.client.send_message(
            entity=user_entity,
            message=message
        )


    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        return None