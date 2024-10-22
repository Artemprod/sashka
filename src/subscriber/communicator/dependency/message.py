import json

from faststream import Context
from faststream.nats import NatsMessage
from loguru import logger

from src.schemas.communicator.message import IncomeUserMessageDTOQueue


async def get_data_from_headers(body: str) -> IncomeUserMessageDTOQueue:
    # Проверка наличия заголовков
    if not body:
        logger.error("Body is missing from the message.")
        raise ValueError("Body is missing from the message.")

    # Извлечение и преобразование значений из заголовков
    try:
        # Попытка валидации данных с использованием Pydantic
        data = IncomeUserMessageDTOQueue.model_validate_json(body)

        # Проверка критических значений
        if not data.from_user:
            logger.error("Missing 'from_user' in headers.")
            raise ValueError("Missing 'from_user' in headers.")

        if not data.client_telegram_id:
            logger.error("Missing 'client_telegram_id' in headers.")
            raise ValueError("Missing 'client_telegram_id' in headers.")

        # Дополнительная проверка на пустоту данных в теле
        if not body.strip():
            logger.error("Empty message body.")
            raise ValueError("Empty message body.")

        # Успешная валидация и создание объекта DTO
        return data

    except (ValueError, TypeError, json.JSONDecodeError) as e:
        # Логируем и выбрасываем ошибку, если что-то пошло не так при валидации
        logger.error(f"Error processing body: {e}")
        raise ValueError("Invalid data in body.") from e
