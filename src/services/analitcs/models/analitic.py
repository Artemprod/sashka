from io import BytesIO
from typing import List

from pydantic import BaseModel

from src.services.analitcs.models.metrics import DialogMetrics

class AnalyticDataDTO(BaseModel):
    class Config:
        from_attributes = True


class AnalyticDataBufferDTO(AnalyticDataDTO):
    dialogs: List[BytesIO]
    metric: DialogMetrics


class AnalyticFileBufferDTO(AnalyticDataDTO):
    dialogs: List[str]
    metric: DialogMetrics
