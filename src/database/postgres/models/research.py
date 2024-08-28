from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase



class Research(ModelBase):
    __tablename__ = 'researches'
    research_id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(String)
    name = Column(String)
    title = Column(String)
    theme = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    updated_id = Column(Integer)
    additional_information = Column(String)
    assistant_id = Column(Integer, ForeignKey('assistants.assistant_id'))

    assistant = relationship("Assistant")
    statuses = relationship("ResearchStatus", back_populates="research")







