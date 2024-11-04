import csv
import io
from datetime import datetime
from pathlib import Path
from typing import List, Union

import pandas as pd
from pydantic import BaseModel, Field


class DialogMetrics(BaseModel):
    """Data class для хранения метрик диалога."""
    total_dialogs: int = Field(description="Общее количество диалогов")
    answered_first: int = Field(description="Количество ответов на первое сообщение")
    conversion_rate: float = Field(description="Процент конверсии")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время создания метрики")








