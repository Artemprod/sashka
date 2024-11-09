import json
from datetime import datetime
from datetime import timezone
from typing import Optional
from typing import Union

from faststream import Context
from faststream.nats import NatsMessage
from loguru import logger
from telethon import TelegramClient

from src.distributor.app.schemas.message import Datas
from src.distributor.app.schemas.message import UserDTOBase
from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer


def get_container(context: Context, container_type: str = "telethon_container") -> Optional[
    Union[ClientsManager, TelethonClientsContainer]]:
    """Возвращает контейнер нужного типа из переданного контекста."""
    container = context.get(container_type)
    if container:
        logger.info(f"Loaded {container_type}")
        return container
    else:
        logger.error(f"No container found for type {container_type}")
        return None


async def _extract_user_from_headers(headers: dict) -> UserDTOBase:
    """Извлекает пользователя из заголовков."""
    user_data = headers.get("user")
    if not user_data:
        logger.error("User header is missing.")
        raise ValueError("User header is missing.")

    user_dict = json.loads(user_data)
    if isinstance(user_dict, dict):
        return UserDTOBase(**user_dict)
    else:
        logger.error("Invalid user header format.")
        raise ValueError("Invalid user header format.")


async def _get_data_from_headers(msg: NatsMessage, context: Context = Context()) -> Datas:
    """Извлекает данные из заголовков сообщения."""
    logger.debug(f"Message headers: {msg.headers}")

    user = await _extract_user_from_headers(msg.headers)
    client_name = msg.headers.get("tg_client") or msg.headers.get("tg_client_name")
    if not client_name:
        logger.error("Missing client name in headers.")
        raise ValueError("Missing client name in headers.")

    container: 'TelethonClientsContainer' = context.get("telethon_container")

    if container is None:
        raise ValueError("Container not found ")

    client: 'TelegramClient' = container.get_telethon_client_by_name(name=client_name)

    current_time = datetime.now(tz=timezone.utc)
    send_time_timestamp = msg.headers.get('send_time_next_message_timestamp')
    send_time = datetime.fromtimestamp(
        float(send_time_timestamp) if send_time_timestamp else current_time.timestamp(),
        tz=timezone.utc
    )
    return Datas(
        user=user,
        client_name=client_name,
        client=client,
        container=container,
        current_time=current_time,
        send_time=send_time,
    )
