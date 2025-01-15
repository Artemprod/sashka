from functools import wraps
from typing import Optional

from loguru import logger
from pydantic import ValidationError
from telethon.tl.types import User

from src.distributor.telegram_client.telethoncl.models.messages import OutcomeMessageDTOQueue
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.services.publisher.publisher import NatsPublisher

publisher = NatsPublisher()


def base_message_handler(subject):
    def decorator(func):
        @wraps(func)
        async def wrapper(event):
            logger.info("Processing message...")
            client_info = await event.client.get_me()
            sender: User = await event.client.get_entity(await event.get_input_sender())

            try:
                s3_key: Optional[str] = await func(event)

                outcome_message = OutcomeMessageDTOQueue(
                    message=str(event.message.message),
                    from_user=str(event.sender_id),
                    first_name=str(sender.first_name) if sender.first_name else "Unknown",
                    username=sender.username,
                    chat=str(event.chat_id),
                    media="None",
                    voice="None",
                    client_telegram_id=str(client_info.id),
                    s3_object_key=s3_key
                ).json_string()
            except ValidationError as ve:
                logger.error(f"Ошибка при валидации заголовков: {ve}")
                return

            try:
                await publisher.publish_message_to_subject(
                    subject_message=NatsQueueMessageDTOSubject(
                        message=outcome_message,
                        subject=subject
                    )
                )
                logger.info("Сообщение успешно опубликовано в очередь!")
            except Exception as e:
                logger.error(f"Ошибка при публикации сообщения: {e}")

        return wrapper
    return decorator
