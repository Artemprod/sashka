from datetime import datetime
from typing import Optional

from openai import BaseModel
from pydantic import Field

from src.database.postgres.models.enum_types import ResearchStatusEnum


class ResearchCashDTO(BaseModel):

    research_id: Optional[int] = None
    research_status: Optional[ResearchStatusEnum] = None
    user_in_progress: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


### Pydantic Модель для заголовоков
class Headers(BaseModel):
    tg_client_name: str = Field(alias="Tg-Client-Name")
    tg_user_userid: str = Field(alias="Tg-User-UserId")
    send_time_msg_timestamp: str = Field(alias="SendTime-Msg-Timestamp")
    send_time_next_message_timestamp: str = Field(alias="SendTime-Next-Message-Timestamp")


### Pydantic Модель для Сообщения
class QUEUEMessage(BaseModel):
    content: str
    subject: str
    stream: str
    headers: Headers

