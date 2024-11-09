from faststream import Context
from faststream.nats import NatsMessage
from loguru import logger



async def get_data_from_headers(body: str, msg: NatsMessage, context=Context()) -> int:
    # Проверка наличия заголовков
    headers = msg.headers
    if not headers:
        logger.error("Headers are missing from the message.")
        raise ValueError("Headers are missing from the message.")

    # Извлечение и преобразование значений из заголовков
    try:
        research_id = int(headers.get("research_id", -1))
        # Проверка критических значений
        if research_id == -1:
            logger.error("Missing user id in headers.")
            raise ValueError("Missing user id in headers.")

        return research_id

    except (ValueError, TypeError) as e:
        logger.error(f"Error processing headers: {e}")
        raise ValueError("Invalid data in headers.") from e
