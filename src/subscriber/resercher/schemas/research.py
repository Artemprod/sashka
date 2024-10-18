from pydantic import BaseModel


class ResearchId(BaseModel):
    research_id: int
