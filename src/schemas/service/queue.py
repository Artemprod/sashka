from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field, validator, field_validator


# Base headers class
class NatsHeaders(BaseModel):
    class Config:
        allow_population_by_field_name = True
        from_attributes = True


class TelegramTimeDelaHeadersDTO(NatsHeaders):
    tg_client_name: str
    user: str
    send_time_msg_timestamp: str
    send_time_next_message_timestamp: str


class TelegramSimpleHeadersDTO(NatsHeaders):
    tg_client_name: str
    tg_user_user_id: str


class TelegramObjectHeadersDTO(NatsHeaders):
    tg_client: str
    user: str


class NatsQueueMessageDTO(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


# Queue message DTO for stream
class NatsQueueMessageDTOStreem(NatsQueueMessageDTO):
    message: str
    subject: str
    stream: str
    headers: Optional[dict] = None


class NatsReplyRequestQueueMessageDTOStreem(NatsQueueMessageDTO):
    subject: str
    stream: Optional[str] = None
    headers: Optional[dict] = None


# Queue message DTO for subject only
class NatsQueueMessageDTOSubject(NatsQueueMessageDTO):
    message: str
    subject: str
    headers: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True
