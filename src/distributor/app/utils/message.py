import asyncio
from typing import Union, Optional

from loguru import logger
from telethon import TelegramClient, types, functions

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


async def send_message_with_typing(
        client: TelegramClient,
        user: UserDTOBase,
        message: str,
        typing_delay: float = 2.0
) -> Optional[types.Message]:
    """
    Отправляет сообщение в Telegram с эффектом печатания и маркировкой прочитанных сообщений.

    Args:
        client: Экземпляр TelegramClient
        user: Объект пользователя с tg_user_id и name
        message: Текст сообщения
        typing_delay: Задержка печатания в секундах

    Returns:
        Optional[types.Message]: Отправленное сообщение или None в случае ошибки
    """

    async def get_entity(user_id: Union[int, str]) -> Optional[types.InputPeerUser]:
        try:
            return await client.get_input_entity(user_id)
        except ValueError as e:
            logger.warning(f"Failed to get entity: {e}")
            return None

    try:
        # Пробуем получить сущность по ID или имени
        user_entity = await get_entity(user.tg_user_id)
        if user_entity is None and user.name:
            user_entity = await get_entity(user.name)

        if user_entity is None:
            raise ValueError("Could not find user entity by ID or username")

        # Отмечаем предыдущие сообщения как прочитанные
        try:
            await client(functions.messages.ReadHistoryRequest(
                peer=user_entity,
                max_id=0
            ))
        except Exception as e:
            logger.warning(f"Failed to mark messages as read: {e}")

        # Устанавливаем статус "печатает"
        try:
            await client(functions.messages.SetTypingRequest(
                peer=user_entity,
                action=types.SendMessageTypingAction()
            ))
        except Exception as e:
            logger.warning(f"Failed to set typing status: {e}")

        # Добавляем задержку для эффекта печатания
        await asyncio.sleep(typing_delay)

        # Отправляем сообщение
        sent_message = await client.send_message(
            entity=user_entity,
            message=message
        )

        return sent_message

    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}", exc_info=True)
        return None