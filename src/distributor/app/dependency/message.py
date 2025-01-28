import json
from datetime import datetime
from datetime import timezone
from typing import Optional
from typing import Union

from faststream import Context
from faststream.nats import NatsMessage
from loguru import logger
from telethon import TelegramClient

from src.distributor.app.schemas.message import Datas, MessageToSendData
from src.distributor.app.schemas.message import UserDTOBase
from src.distributor.telegram_client.pyro.client.container import ClientsManager
from src.distributor.telegram_client.telethoncl.manager.container import TelethonClientsContainer


def get_container(
    context: Context, container_type: str = "telethon_container"
) -> Optional[Union[ClientsManager, TelethonClientsContainer]]:
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


async def _get_data_from_headers(body: str, msg: NatsMessage, context: Context = Context()) -> Datas:
    """Извлекает данные из заголовков сообщения."""

    logger.debug(f"Message headers: {msg.headers}")

    user = await _extract_user_from_headers(msg.headers)
    client_name = msg.headers.get("tg_client") or msg.headers.get("tg_client_name")
    if not client_name:
        logger.error("Missing client name in headers.")
        raise ValueError("Missing client name in headers.")

    container: "TelethonClientsContainer" = context.get("telethon_container")

    if container is None:
        raise ValueError("Container not found ")

    client: "TelegramClient" = container.get_telethon_client_by_name(name=client_name)

    current_time = datetime.now(tz=timezone.utc)
    send_time_timestamp = msg.headers.get("send_time_next_message_timestamp")
    send_time = datetime.fromtimestamp(
        float(send_time_timestamp) if send_time_timestamp else current_time.timestamp(), tz=timezone.utc
    )
    return Datas(
        user=user,
        client_name=client_name,
        client=client,
        container=container,
        current_time=current_time,
        send_time=send_time,
    )


async def get_data_from_body(body: str) -> MessageToSendData:
    if not body:
        logger.error("Body is missing from the message.")
        raise ValueError("Body is missing from the message.")

    try:
        data = json.loads(body)

        # Декодировать строковый JSON в объект для user
        if isinstance(data.get("user"), str):
            data["user"] = json.loads(data["user"])
        # Валидация с использованием Pydantic
        validated_data = MessageToSendData(**data)

        if not validated_data.message:
            logger.warning("Missing Message")
            validated_data.message = ""

        if not validated_data.user:
            logger.error("Missing user data.")
            raise ValueError("Missing user data")

        return validated_data

    except (ValueError, TypeError, json.JSONDecodeError) as e:
        logger.error(f"Error processing body: {e}")


async def get_telegram_client(body: str, context: Context = Context()) -> TelegramClient:
    """Извлекает клиента."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON body. {body}")
        raise ValueError("Invalid JSON format.") from e

    client_name = data.get("tg_client") or data.get("tg_client_name")
    if not client_name:
        logger.error("Client name not provided in the body.")
        raise ValueError("Client name is missing in the JSON body.")

    container: "TelethonClientsContainer" = context.get("telethon_container")
    if container is None:
        logger.error("Container not found in context.")
        raise ValueError("Container not found in context.")

    client: "TelegramClient" = container.get_telethon_client_by_name(name=client_name)
    if not client:
        logger.error(f"No Telegram client found with the name: {client_name}")
        raise ValueError("No Telegram client found.")

    return client


async def get_telegram_client_name(body: str) -> str:
    """Извлекает клиента."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON body. {body}")
        raise ValueError("Invalid JSON format.") from e

    client_name = data.get("tg_client") or data.get("tg_client_name")
    if not client_name:
        logger.error("Client name not provided in the body.")
        raise ValueError("Client name is missing in the JSON body.")

    return client_name


async def get_research_id(body: str) -> int:
    """Извлекает id исследования."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON body. {body}")
        raise ValueError("Invalid JSON format.") from e

    research_id = data.get("research_id")
    logger.info(f"Body: {body} RESEARCH ID {research_id}")
    if not research_id:
        logger.error("research_id not provided in the body.")
        raise ValueError("research_id is missing in the JSON body.")

    return int(research_id)
