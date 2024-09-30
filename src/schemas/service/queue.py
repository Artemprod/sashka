from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Base headers class
class NatsHeaders(BaseModel):
    ...


# class Headers(BaseModel):
#     tg_client_name: str = Field(alias="Tg-Client-Name")
#     tg_user_userid: str = Field(alias="Tg-User-UserId")
#     send_time_msg_timestamp: str = Field(alias="SendTime-Msg-Timestamp")
#     send_time_next_message_timestamp: str = Field(alias="SendTime-Next-Message-Timestamp")
#
#
# class SimpleHeaders(BaseModel):
#     tg_client_name: str = Field(alias="Tg-Client-Name")
#     tg_user_userid: str = Field(alias="Tg-User-UserId")


# Telegram specific headers inheriting from base headers
class NatsTelegramHeaders(NatsHeaders):
    telegram_client_name: Optional[str] = None
    tg_user_id: Optional[str] = None
    description: Optional[str] = None
    send_time: Optional[datetime] = Field(default_factory=lambda: datetime.now())


# Queue message DTO for stream
class NatsQueueMessageDTOStreem(BaseModel):
    message: str
    subject: str
    stream: str
    headers: Optional[NatsHeaders] = None

    class Config:
        arbitrary_types_allowed = True


# Queue message DTO for subject only
class NatsQueueMessageDTOSubject(BaseModel):
    message: str
    subject: str
    headers: Optional[NatsHeaders] = None

    class Config:
        arbitrary_types_allowed = True


# Rebuild the models if necessary
NatsHeaders.model_rebuild()
NatsQueueMessageDTOStreem.model_rebuild()
NatsQueueMessageDTOSubject.model_rebuild()
