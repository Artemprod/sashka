from faststream import Context
from faststream.nats import NatsMessage
from loguru import logger

from src.schemas.communicator.message import IncomeUserMessageDTOQueue


async def get_data_from_headers(body: str, msg: NatsMessage, context=Context()) -> IncomeUserMessageDTOQueue:
    # Проверка наличия заголовков
    headers = msg.headers
    if not headers:
        logger.error("Headers are missing from the message.")
        raise ValueError("Headers are missing from the message.")

    # Извлечение и преобразование значений из заголовков
    try:
        from_user = int(headers.get("from_user", 0))
        chat = int(headers.get("chat", from_user))  # Используем from_user, если chat отсутствует
        user_name = headers.get("user_name", "Unknown")
        media = headers.get("media", "false").lower() == "true"
        voice = headers.get("voice", "false").lower() == "true"
        client_telegram_id = int(headers.get("client_telegram_id", 0))

        # Проверка критических значений
        if from_user == 0:
            logger.error("Missing user id in headers.")
            raise ValueError("Missing user id in headers.")

        if client_telegram_id == 0:
            logger.error("Missing client telegram id in headers.")
            raise ValueError("Missing client telegram id in headers.")

        if not body:
            logger.error("Empty message body.")
            raise ValueError("Empty message body.")

        # Создание объекта IncomeUserMessageDTOQueue
        return IncomeUserMessageDTOQueue(
            from_user=from_user,
            chat=chat,
            user_name=user_name,
            media=media,
            voice=voice,
            text=body,
            client_telegram_id=client_telegram_id,
        )

    except (ValueError, TypeError) as e:
        logger.error(f"Error processing headers: {e}")
        raise ValueError("Invalid data in headers.") from e
