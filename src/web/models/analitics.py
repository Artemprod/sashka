from enum import Enum

from pydantic import BaseModel
from pydantic import Field

from src.web.models.client import ClientConfigDTO
from enum import Enum
from pydantic import BaseModel

class ResearchStatus(str, Enum):
    done = "done"
    in_progress = "in_progress"

class AnalyticDTO(BaseModel):
    research_status: ResearchStatus
    research_id: int

    class Config:
        from_attributes = True




