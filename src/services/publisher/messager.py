import asyncio
from typing import Dict

from faststream.nats import NatsBroker
from loguru import logger

from src.schemas.queue import NatsTelegramHeaders, NatsQueueMessageDTOStreem, NatsQueueMessageDTOSubject


class NatsPublisher:
    def __init__(self):
        self.settings = self._load_settings()

    @staticmethod
    def _load_settings() -> Dict[str, str]:
        return {
            "nats_server": "nats://localhost:4222"
        }

    async def publish_message_to_subject(self, subject_message: NatsQueueMessageDTOSubject) -> None:
        try:
            async with NatsBroker(self.settings["nats_server"]) as broker:
                await broker.publish(message=subject_message.message,
                                     subject=subject_message.subject,
                                     headers=subject_message.headers)

                logger.info(f"Сообщение успешно отправлено на тему {subject_message.subject}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения на тему {subject_message.subject}: {e}")

    async def publish_message_to_stream(self, stream_message: NatsQueueMessageDTOStreem) -> None:
        try:
            async with NatsBroker(self.settings["nats_server"]) as broker:
                await broker.publish(
                    message=stream_message.message,
                    subject=stream_message.subject,
                    stream=stream_message.stream,
                    headers=stream_message.headers
                )
                logger.info(f"Сообщение успешно отправлено на стрим {stream_message.stream}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения на стрим {stream_message.stream}: {e}")




async def main():
    # Пример использования
    publisher = NatsPublisher()
    message_dto = NatsQueueMessageDTOStreem(
        message="Пример сообщения",
        subject="example.subject",
        stream="example.stream",
        headers=None
    )

    await publisher.publish_message_to_stream(message_dto)


if __name__ == '__main__':
    asyncio.run(main())
