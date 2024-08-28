from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.database.postgres.models.base import ModelBase




class UserResearch(ModelBase):
    __tablename__ = 'user_research'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime)
    status_id = Column(Integer, ForeignKey('research_status_name.status_id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    research_id = Column(Integer, ForeignKey('researches.research_id'))

    user = relationship("User", back_populates="researches")
    research = relationship("Research")
    status = relationship("ResearchStatusName")
