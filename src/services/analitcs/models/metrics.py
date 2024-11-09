from datetime import datetime

from pydantic import BaseModel, Field


class DialogMetrics(BaseModel):
    """Data class для хранения метрик диалога."""
    total_dialogs: int = Field(description="Общее количество диалогов")
    answered_first: int = Field(description="Количество ответов на первое сообщение")
    conversion_rate: float = Field(description="Процент конверсии")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время создания метрики")








