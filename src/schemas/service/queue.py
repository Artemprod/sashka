from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, field_validator


# Base headers class
class NatsHeaders(BaseModel):

    class Config:
        allow_population_by_field_name = True


class TelegramTimeDelaHeadersDTO(NatsHeaders):
    tg_client_name: str = Field(alias="Tg-Client-Name")
    tg_user_userid: str = Field(alias="Tg-User-UserId")
    send_time_msg_timestamp: str = Field(alias="SendTime-Msg-Timestamp")
    send_time_next_message_timestamp: str = Field(alias="SendTime-Next-Message-Timestamp")


class TelegramSimpleHeadersDTO(NatsHeaders):
    tg_client_name: str = Field(alias="Tg-Client-Name")
    tg_user_userid: str = Field(alias="Tg-User-UserId")


class NatsQueueMessageDTO(BaseModel):
    class Config:
        arbitrary_types_allowed = True


# Queue message DTO for stream
class NatsQueueMessageDTOStreem(NatsQueueMessageDTO):
    message: str
    subject: str
    stream: str
    headers: Optional[dict] = None


# Queue message DTO for subject only
class NatsQueueMessageDTOSubject(NatsQueueMessageDTO):
    message: str
    subject: str
    headers: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True
