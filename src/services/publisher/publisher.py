import asyncio
from typing import Dict
from typing import Optional
from typing import Union

from faststream.nats import NatsBroker
from loguru import logger

from configs.nats_queues import nast_base_settings
from src.schemas.service.queue import NatsQueueMessageDTOStreem
from src.schemas.service.queue import NatsQueueMessageDTOSubject
from src.schemas.service.queue import NatsReplyRequestQueueMessageDTOStreem


class NatsPublisher:
    def __init__(self):
        self.settings = self._load_settings()

    # TODO заменить на актулдьнае настройки
    @staticmethod
    def _load_settings() -> Dict[str, Union[str, int, float]]:
        return {
            "nats_server": nast_base_settings.nats_server_url,
            "MAX_RETRIES": nast_base_settings.rpc.max_retries,
            "RPC_TIMEOUT": nast_base_settings.rpc.timeout,
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

    async def request_reply(self, nats_message: NatsReplyRequestQueueMessageDTOStreem) -> Optional[str]:
        async with NatsBroker(self.settings["nats_server"]) as broker:
            for attempt in range(1, self.settings["MAX_RETRIES"] + 1):
                try:
                    logger.info(f"Отправка запроса: Попытка {attempt}")
                    response = await self._send_request(broker, nats_message)
                    if response:
                        logger.info(f"Ответ от сервера: {response}")
                        return response
                    else:
                        logger.warning(f"Не удалось получить ответ: Попытка {attempt}")
                except asyncio.TimeoutError:
                    logger.error(f"Время ожидания ответа истекло: Попытка {attempt}")
                except Exception as e:
                    logger.error(f"Произошла ошибка: {e}. Попытка {attempt}")

            logger.error(f"Не удалось получить ответ после {self.settings['MAX_RETRIES']} попыток.")
            return None

    async def _send_request(self, broker: NatsBroker,
                            nats_message: NatsReplyRequestQueueMessageDTOStreem) -> Optional[str]:

        return await broker.publish(
            headers=nats_message.headers,
            subject=nats_message.subject,
            message=b'',
            rpc=True,
            rpc_timeout=self.settings["RPC_TIMEOUT"],
        )

    @staticmethod
    def form_stream_message(message: str,
                            subject: str,
                            stream: str,
                            headers: Dict[str, str] = None) -> NatsQueueMessageDTOStreem:
        return NatsQueueMessageDTOStreem(
            message=message,
            subject=subject,
            stream=stream,
            headers=headers,
        )

    @staticmethod
    def form_subject_message() -> NatsQueueMessageDTOSubject:
        return NatsQueueMessageDTOSubject()



