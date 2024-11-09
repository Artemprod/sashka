from io import BytesIO
from typing import List

from pydantic import BaseModel


class AnalyticDataDTO(BaseModel):
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class AnalyticDataBufferDTO(AnalyticDataDTO):
    dialogs: List[BytesIO]
    metric: BytesIO

class AnalyticFileDTO(AnalyticDataDTO):
    dialogs: List[str]
    metric: str



