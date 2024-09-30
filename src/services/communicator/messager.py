from abc import ABC
from typing import Union

from src.schemas.service.queue import NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem
from src.services.publisher.messager import NatsPublisher


class Message(ABC):

    def __init__(self, publisher: NatsPublisher):
        self.publisher = publisher

    async def publish_message(self, queue_object: Union[NatsQueueMessageDTOSubject, NatsQueueMessageDTOStreem]):

        if isinstance(queue_object, NatsQueueMessageDTOSubject):
            try:
                await self.publisher.publish_message_to_subject(subject_message=queue_object)
            except Exception as e:
                raise e

        elif isinstance(queue_object, NatsQueueMessageDTOStreem):
            try:
                await self.publisher.publish_message_to_stream(stream_message=queue_object)
            except Exception as e:
                raise e


class MessageFirstSend(Message):
    ...


class MessageAnswer(Message):
    ...


class MessageSend(Message):
    ...
